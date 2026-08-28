export default function ErrorMessage({ id, message }) {
  if (!message) {
    return null;
  }

  return (
    <p id={id} className="mt-2 text-sm font-medium text-red-700" role="alert">
      {message}
    </p>
  );
}

