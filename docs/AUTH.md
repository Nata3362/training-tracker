# Authentication: design

A portable module — see the diagram
([Splitting the Sheet](https://claude.ai/code/artifact/56535e2a-6c4e-4c76-b59a-c61fbe2a9573),
figure 3) for the picture. This is the same design in prose + code: what to build,
why this shape and not another, and exactly how a protected route checks who's
asking.

Nothing in this module knows what a workout is. It only knows `users` and
`sessions`. The workout tracker plugs into it at two points — noted where they
come up below.

**As built**, "the module" is a real package, `backend/app/authentication/`,
that never imports `Person` *and defines no HTTP endpoints* — the code
samples below read as one file with routes for clarity, but the plain
functions map onto `authentication/models.py`, `security.py`, and `auth.py`,
while every route (including the ones with no `Person` involvement at all,
like login) lives in `backend/app/composition.py`. That file is `signup()`'s
"app hook" from §5 made literal, and it's the only place that imports both
`app.authentication` and `app.models`. The identity endpoint is `GET /user`,
not `/me` as sampled in an earlier design pass; the real handler also inlines
the `User`/`Person` join directly rather than through a separate
`get_identity()` function, since it has exactly one caller — §5's sample
keeps the split for readability. See [docs/setup.md](setup.md) §2 for the
current file map.

---

## 1. The approach, and what it's not

**Server-side sessions, referenced by an opaque cookie token.** Login creates a
row in a `sessions` table and hands the browser a random token that means
nothing on its own; every request looks that token up to find out who's asking.

This is the same pattern Django, Rails, and Flask-Login all default to — not a
custom scheme. The two alternatives, and why they're not the pick here:

- **Stateless JWT** (a signed token that carries the user info, no DB lookup per
  request). Standard for SPA-to-API and microservices that don't share a
  session store. The catch: you can't revoke one before it expires without
  adding a blocklist — which is a sessions table again, just for revocations
  only. Skip it unless something forces statelessness (multiple independent
  services checking auth without hitting the same DB).
- **Hosted auth** (Supabase Auth, Clerk, Auth0, Firebase Auth). If the DB ends
  up on Supabase, it ships full auth for free on the same Postgres instance —
  worth checking before building this, since it may make the module below
  unnecessary rather than merely portable.

For a handful of users, DB-backed sessions are the boring, standard choice —
easy to reason about, and logout (or "log out everywhere") is one `DELETE`.

---

## 2. Schema

Same `Base` as [ARCHITECTURE.md](ARCHITECTURE.md) §3 — these models live
alongside `Person`, `Exercise`, etc. and get created together, since nothing
exists yet. The session model is named `AuthSession`, not `Session` — that
name's already taken by `sqlalchemy.orm.Session`, and shadowing it is a
mistake worth naming rather than tripping over later.

```python
from datetime import datetime, timezone
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base   # the Base from ARCHITECTURE.md §3


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class AuthSession(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    token_hash: Mapped[str] = mapped_column(unique=True, index=True)  # sha256 of the token, never the raw token
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime]
```

`sessions` stores a **hash** of the token, the same reasoning as password
hashing: a leaked `sessions` table shouldn't hand out working logins.

**The one wire into this app**: `Person.user_id` in
[ARCHITECTURE.md](ARCHITECTURE.md) §3 already carries
`ForeignKey("users.id")` — it's part of the model from the start, not a
column bolted on afterward. A different project wires its own "owning"
table to `users.id` the same way, on the model, before it's ever created.

---

## 3. Password hashing

`hashlib.scrypt` — stdlib, no new dependency, memory-hard (deliberately slow
to brute-force, unlike a plain `sha256`).

```python
import hashlib
import hmac
import secrets

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt.hex() + "$" + digest.hex()

def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.scrypt(
        password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1
    )
    return hmac.compare_digest(digest, bytes.fromhex(digest_hex))  # constant-time

# self-check
if __name__ == "__main__":
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h)
    assert not verify_password("wrong password", h)
    print("ok")
```

`n=2**14` (16384) is scrypt's CPU/memory cost — the 2017 OWASP-cited minimum.
Raise it if login latency has headroom to spare; it's the one knob here that
trades security for speed, so it's worth revisiting once real hardware is
known, not left at a guess forever.

---

## 4. Session lifecycle

```python
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DBSession

SESSION_TTL = timedelta(days=30)

def create_session(db: DBSession, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.add(AuthSession(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=datetime.now(timezone.utc) + SESSION_TTL,
    ))
    db.commit()
    return token  # the raw token goes in the cookie; only its hash is ever stored

def verify_session(db: DBSession, token: str) -> int | None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    row = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_hash,
            AuthSession.expires_at > datetime.now(timezone.utc),
        )
    )
    return row.user_id if row else None

def revoke_session(db: DBSession, token: str) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash))
    db.commit()
```

"Log out everywhere" is
`db.execute(delete(AuthSession).where(AuthSession.user_id == user_id))` — no
token needed, which is the whole point of keeping sessions server-side.

---

## 5. `require_auth()` — how a protected route actually checks

This is the seam every other route in the app depends on. It reads the
session cookie, resolves it to a `user_id` via `verify_session()`, and either
returns that `user_id` or the request never reaches the route body.

Every route below depends on `get_db`, the standard FastAPI + SQLAlchemy
pattern — one session per request, closed when the request ends:

```python
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

app = FastAPI()

async def require_auth(
    session: str | None = Cookie(default=None),
    db: DBSession = Depends(get_db),
) -> int:
    if session is None:
        raise HTTPException(401, "Not logged in")
    user_id = verify_session(db, session)
    if user_id is None:
        raise HTTPException(401, "Session expired or invalid")
    return user_id
```

**Example: signup, login, and a protected route using it.**

```python
@app.post("/auth/signup")
def signup(payload: SignupBody, response: Response, db: DBSession = Depends(get_db)):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(409, "Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()  # assigns user.id without committing yet

    # app hook — the module doesn't know about `Person`, the app wires it here
    db.add(Person(user_id=user.id, name=payload.name))
    db.commit()

    token = create_session(db, user.id)
    response.set_cookie("session", token, httponly=True, secure=True, samesite="lax")
    return {"ok": True}


@app.post("/auth/login")
def login(payload: LoginBody, response: Response, db: DBSession = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    token = create_session(db, user.id)
    response.set_cookie("session", token, httponly=True, secure=True, samesite="lax")
    return {"ok": True}


@app.post("/auth/logout")
def logout(response: Response, session: str | None = Cookie(default=None), db: DBSession = Depends(get_db)):
    if session:
        revoke_session(db, session)
    response.delete_cookie("session")
    return {"ok": True}


# --- outside the module: the app hook, made literal --------------------------

def get_identity(db: DBSession, user_id: int) -> dict:
    user = db.get(User, user_id)
    person = db.scalar(select(Person).where(Person.user_id == user_id))
    return {"id": user.id, "email": user.email, "name": person.name}


@app.get("/user")
def user(user_id: int = Depends(require_auth), db: DBSession = Depends(get_db)):
    return get_identity(db, user_id)


# --- an existing route from ARCHITECTURE.md, now protected ------------------

@app.get("/workouts/today")
def get_todays_workout(user_id: int = Depends(require_auth), db: DBSession = Depends(get_db)):
    person = db.scalar(select(Person).where(Person.user_id == user_id))
    return load_workout(db, person)   # domain function from ARCHITECTURE.md §4
```

**`/user` is what makes a browser frontend possible at all.** `httponly`
means JS can't read the cookie, so "am I logged in?" can only be answered by
asking the server. The frontend calls it once on load and treats a `401` as
logged out — without it, a page refresh (which wipes all client state but
keeps the cookie) would show the login form to someone already logged in. It
joins `User` and `Person`, since a display name has to come from somewhere.

`/user` isn't defined *inside* the module, though — the module exposes plain
functions only, no FastAPI routes at all. It lives in the composition file
(`app/composition.py` in this codebase), which is the "app hook" from §2 and
§5's `signup()` made literal, not just commented: nothing under
`app/authentication/` imports `Person`, or decides an HTTP path or status
code. A different project reusing this module gets
`create_user`/`authenticate_user`/`require_auth` for free and writes a
handful of one-line route wrappers around them, plus its own identity join
for whatever "owning" table it wired up in §2.

*(An earlier pass also had a pure, `Person`-free `/auth/me` inside the same
composition file, for a consumer that needs "is this session valid" without a
name. Dropped as redundant here — one frontend, one consumer, no reason yet
to keep two identity endpoints. Worth resurrecting if a second consumer shows
up that must stay ignorant of the domain schema.)*

**`/user`'s id is not for the frontend to send back.** The frontend
holds `person_id` (from `/user`) for display and for comparing against
multi-person data it already has (e.g. bolding "your" row in a shared `/prs`
list) — never as a parameter to ask for data
(`/workouts/today?person_id=…`), which would let anyone read another
person's log by editing a number. Protected routes derive the person from
the cookie themselves, exactly as `get_todays_workout` does above — the
client presents a cookie, never a claim about who it is.

What `Depends(require_auth)` buys: FastAPI runs `require_auth` **before**
`get_todays_workout`'s body. If the cookie is missing or the session's
expired, the client gets a 401 and `get_todays_workout` never executes — the
route body can assume `user_id` is real and never re-check it. Every other
protected route (`POST /sessions`, `GET /log`, `/history`, `/prs`,
`/charts/*`) takes the identical one-line dependency; that repetition across
routes is the "wraps every protected route" arrow in the diagram.

---

## 6. Operational notes

- **Cookie flags**: `httponly` (JS can't read it — blocks token theft via
  XSS), `secure` (HTTPS only), `samesite=lax` (blocks it being sent on
  cross-site POSTs — basic CSRF protection for free).
- **`samesite=lax` constrains deployment**, which is easy to miss until it
  silently breaks: the frontend and the API must be the *same site* (one
  registrable domain), or the browser won't even store the cookie the login
  response sets. Two `*.up.railway.app` services are *not* same-site —
  Railway is on the Public Suffix List. Hence `www.natoli.dk` +
  `api.natoli.dk`; see [DEPLOY.md](DEPLOY.md) §4. Locally the same rule
  applies: use `localhost` for both, never `localhost` for one and
  `127.0.0.1` for the other.
- **CORS is a separate gate.** `allow_credentials=True` plus the exact origin
  (never `*`) lets the frontend *read* the response; `SameSite` decides
  whether the cookie is stored and sent at all. Both must pass.
- **Session cleanup**: expired rows aren't deleted automatically. Either a
  daily job running
  `db.execute(delete(AuthSession).where(AuthSession.expires_at < datetime.now(timezone.utc)))`,
  or skip it and let `verify_session()`'s `expires_at > now()` check make
  expired rows inert — cleanup then becomes housekeeping, not correctness.
  Fine to defer until the table's size is actually a problem.
- **Rate limiting login/signup** is out of scope here — add it at the reverse
  proxy or gateway if this ever faces the public internet instead of two
  known people.

---

## 7. Deliberately out of scope

- Email verification, password reset flows — same shape as signup (a
  time-limited token in a table), add when needed rather than speculatively.
- Social login (Google, etc.) — changes the module's shape (provider
  callback, linking multiple providers to one `user_id`); say if that's
  coming so it's designed in rather than bolted on.
- Roles/permissions — every logged-in user is currently equivalent (their own
  `people` row via `user_id`). No admin/shared-data concept exists yet.
