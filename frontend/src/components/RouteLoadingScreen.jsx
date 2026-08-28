export default function RouteLoadingScreen() {
  return (
    <div className="flex min-h-[55vh] items-center justify-center px-4" role="status">
      <div className="text-center">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
        <p className="mt-4 text-sm font-semibold text-slate-700">Loading page...</p>
      </div>
    </div>
  );
}

