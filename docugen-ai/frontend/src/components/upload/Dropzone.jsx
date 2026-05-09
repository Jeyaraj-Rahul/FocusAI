import { UploadCloud } from "lucide-react";
import { useCallback, useState } from "react";

export default function Dropzone({ accept, label = "Upload files", hint = "Drag files here or click to browse", onFiles, disabled = false }) {
  const [dragging, setDragging] = useState(false);

  const handleFiles = useCallback(
    (fileList) => {
      const files = Array.from(fileList || []);
      if (files.length && onFiles) onFiles(files);
    },
    [onFiles]
  );

  return (
    <label
      className={`block rounded-lg border-2 border-dashed p-8 text-center transition ${
        dragging
          ? "border-blue-500 bg-blue-50 dark:bg-blue-950/30"
          : "border-slate-300 bg-white hover:border-blue-400 dark:border-slate-700 dark:bg-slate-900"
      } ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}`}
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        if (!disabled) handleFiles(event.dataTransfer.files);
      }}
    >
      <input
        className="sr-only"
        type="file"
        accept={accept}
        disabled={disabled}
        onChange={(event) => handleFiles(event.target.files)}
      />
      <UploadCloud className="mx-auto h-9 w-9 text-blue-500" />
      <p className="mt-3 font-medium text-slate-900 dark:text-white">{label}</p>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{hint}</p>
    </label>
  );
}
