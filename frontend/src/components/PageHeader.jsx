export default function PageHeader({ eyebrow, title, description }) {
  return (
    <header className="mx-auto mb-10 max-w-3xl text-center">
      {eyebrow ? (
        <span className="mb-3 inline-block rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-1 text-xs font-mono font-bold uppercase tracking-widest text-emerald-400 backdrop-blur-md">
          {eyebrow}
        </span>
      ) : null}
      <h1 className="mt-2 text-3xl font-black tracking-tight text-white sm:text-4xl">
        {title}
      </h1>
      {description ? (
        <p className="mt-4 text-sm sm:text-base leading-relaxed text-slate-300">
          {description}
        </p>
      ) : null}
    </header>
  );
}


