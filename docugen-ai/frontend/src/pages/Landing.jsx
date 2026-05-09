import { Link } from "react-router-dom";
import Button from "../components/common/Button.jsx";

export default function Landing() {
  return (
    <section className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6">
      <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">Starter scaffold</p>
      <h1 className="mt-3 text-4xl font-bold tracking-normal text-slate-950">DocuGen AI</h1>
      <p className="mt-4 max-w-2xl text-slate-600">
        Production-ready project architecture for an AI-powered document automation platform.
      </p>
      <div className="mt-6">
        <Link to="/app">
          <Button>Open App Shell</Button>
        </Link>
      </div>
    </section>
  );
}
