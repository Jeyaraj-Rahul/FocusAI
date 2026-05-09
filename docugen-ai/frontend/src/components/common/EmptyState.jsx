import Button from "./Button.jsx";

export default function EmptyState({ icon, title, description, actionLabel, onAction }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center dark:border-slate-700 dark:bg-slate-950">
      <div className="mx-auto grid h-12 w-12 place-items-center rounded-md bg-white text-slate-500 shadow-sm dark:bg-slate-900 dark:text-slate-300">
        {icon}
      </div>
      <h3 className="mt-4 font-semibold text-slate-950 dark:text-white">{title}</h3>
      <p className="mx-auto mt-2 max-w-sm text-sm text-slate-500 dark:text-slate-400">{description}</p>
      {actionLabel ? (
        <Button className="mt-5" onClick={onAction}>
          {actionLabel}
        </Button>
      ) : null}
    </div>
  );
}
