import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";

interface ModalDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  subtitle?: string;
  icon: React.ReactNode;
  iconClassName?: string;
  panelClassName?: string;
  headerClassName?: string;
  alignBottomOnMobile?: boolean;
  children: React.ReactNode;
}

export const ModalDrawer: React.FC<ModalDrawerProps> = ({
  isOpen,
  onClose,
  title,
  subtitle,
  icon,
  iconClassName = "bg-[#bd93f9]/15 text-[#bd93f9] border-[#bd93f9]/30",
  panelClassName = "max-w-lg rounded-t-lg sm:rounded-lg",
  headerClassName = "px-5 py-4",
  alignBottomOnMobile = true,
  children,
}) => {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (isOpen && !dialog.open) {
      dialog.showModal();
    } else if (!isOpen && dialog.open) {
      dialog.close();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <dialog
      ref={dialogRef}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === dialogRef.current) onClose();
      }}
      className={`fixed inset-0 m-0 max-w-none max-h-none w-full h-full bg-transparent p-0 ${
        alignBottomOnMobile ? "sm:p-4 flex items-end sm:items-center" : "p-4 flex items-center"
      } justify-center`}
    >
      <div
        className={`w-full bg-[#282a36] border border-[#44475a] shadow-2xl overflow-hidden text-[#f8f8f2] ${panelClassName}`}
      >
        <div
          className={`flex items-center justify-between border-b border-[#44475a]/60 bg-[#282a36] ${headerClassName}`}
        >
          <div className="flex items-center gap-2.5">
            <div className={`p-1.5 rounded-md border ${iconClassName}`}>{icon}</div>
            <div>
              <h3 className="text-sm font-semibold text-[#f8f8f2]">{title}</h3>
              {subtitle && <p className="text-[11px] text-[#6272a4]">{subtitle}</p>}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-md text-[#6272a4] hover:text-[#f8f8f2] hover:bg-[#44475a]/50 transition-all"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
        {children}
      </div>
    </dialog>
  );
};
