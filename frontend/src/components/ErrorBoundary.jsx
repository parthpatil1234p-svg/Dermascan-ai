import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="flex min-h-screen items-center justify-center bg-clinic-50 px-4">
          <section className="w-full max-w-lg border-y border-slate-200 bg-white py-10 text-center">
            <h1 className="text-2xl font-bold text-slate-950">
              This page could not be displayed
            </h1>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              No analysis result was changed. Return home and retry the workflow.
            </p>
            <a
              href="/"
              className="mt-6 inline-flex rounded-lg bg-brand-600 px-5 py-3 text-sm font-semibold text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
            >
              Return Home
            </a>
          </section>
        </main>
      );
    }
    return this.props.children;
  }
}

