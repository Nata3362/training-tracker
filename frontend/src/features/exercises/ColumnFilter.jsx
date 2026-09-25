import { useEffect, useRef, useState } from "react";

// A clickable table-header label that opens a dropdown of filter options.
// The menu is position: fixed so the table wrapper's overflow can't clip it.
function ColumnFilter({ label, options, value, onChange }) {
    const [open, setOpen] = useState(false);
    const [position, setPosition] = useState(null);
    const buttonRef = useRef(null);
    const menuRef = useRef(null);

    useEffect(() => {
        if (!open) return undefined;

        function handlePointerDown(event) {
            if (!buttonRef.current.contains(event.target) && !menuRef.current?.contains(event.target)) {
                setOpen(false);
            }
        }

        function handleKeyDown(event) {
            if (event.key === "Escape") {
                setOpen(false);
                buttonRef.current.focus();
            }
        }

        // The fixed position goes stale once the page moves, so just close.
        function close() {
            setOpen(false);
        }

        document.addEventListener("pointerdown", handlePointerDown);
        document.addEventListener("keydown", handleKeyDown);
        window.addEventListener("resize", close);
        window.addEventListener("scroll", close, true);

        return () => {
            document.removeEventListener("pointerdown", handlePointerDown);
            document.removeEventListener("keydown", handleKeyDown);
            window.removeEventListener("resize", close);
            window.removeEventListener("scroll", close, true);
        };
    }, [open]);

    function toggle() {
        if (!open) {
            const rect = buttonRef.current.getBoundingClientRect();
            setPosition({ top: rect.bottom + 6, left: rect.left });
        }
        setOpen((current) => !current);
    }

    function choose(nextValue) {
        onChange(nextValue);
        setOpen(false);
        buttonRef.current.focus();
    }

    const activeLabel = options.find(([optionValue]) => optionValue === value)?.[1];

    return (
        <>
            <button
                ref={buttonRef}
                type="button"
                className={value ? "column-filter active" : "column-filter"}
                aria-haspopup="menu"
                aria-expanded={open}
                onClick={toggle}
            >
                {label}{activeLabel && `: ${activeLabel}`}
                <span aria-hidden="true"> ▾</span>
            </button>
            {open && (
                <div ref={menuRef} className="column-filter-menu" role="menu" aria-label={label} style={position}>
                    {[["", "All"], ...options].map(([optionValue, optionLabel]) => (
                        <button
                            key={optionValue || "all"}
                            type="button"
                            role="menuitemradio"
                            aria-checked={optionValue === value}
                            onClick={() => choose(optionValue)}
                        >
                            {optionLabel}
                        </button>
                    ))}
                </div>
            )}
        </>
    );
}

export default ColumnFilter;
