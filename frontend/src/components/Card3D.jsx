import { useRef, useState } from "react";

/**
 * Card3D - High-performance physics-based 3D tilt card component
 * Provides reactive 3D perspective rotation and dynamic specular spotlight highlight.
 */
export default function Card3D({
  children,
  className = "",
  glowColor = "emerald", // "emerald" | "cyan" | "violet" | "brand"
  maxTilt = 12,
  glare = true,
  onClick,
}) {
  const cardRef = useRef(null);
  const [transformStyle, setTransformStyle] = useState("");
  const [glarePosition, setGlarePosition] = useState({ x: 50, y: 50, opacity: 0 });

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -maxTilt;
    const rotateY = ((x - centerX) / centerX) * maxTilt;

    setTransformStyle(
      `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.02, 1.02, 1.02)`
    );

    if (glare) {
      setGlarePosition({
        x: (x / rect.width) * 100,
        y: (y / rect.height) * 100,
        opacity: 0.25,
      });
    }
  };

  const handleMouseLeave = () => {
    setTransformStyle("perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)");
    setGlarePosition((prev) => ({ ...prev, opacity: 0 }));
  };

  const glowStyles = {
    emerald: "hover:border-emerald-500/40 hover:shadow-[0_20px_45px_-10px_rgba(16,185,129,0.25)]",
    cyan: "hover:border-cyan-500/40 hover:shadow-[0_20px_45px_-10px_rgba(6,182,212,0.25)]",
    violet: "hover:border-violet-500/40 hover:shadow-[0_20px_45px_-10px_rgba(139,92,246,0.25)]",
    brand: "hover:border-brand-500/40 hover:shadow-[0_20px_45px_-10px_rgba(20,184,166,0.25)]",
  };

  return (
    <div
      ref={cardRef}
      onClick={onClick}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        transform: transformStyle,
        transition: "transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1), border-color 0.3s ease, box-shadow 0.3s ease",
        transformStyle: "preserve-3d",
      }}
      className={`relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white/90 backdrop-blur-xl shadow-soft transition-shadow duration-300 dark:border-white/10 dark:bg-slate-900/80 ${glowStyles[glowColor] || glowStyles.emerald} ${className}`}
    >
      {glare && (
        <div
          className="pointer-events-none absolute -inset-px transition-opacity duration-300"
          style={{
            opacity: glarePosition.opacity,
            background: `radial-gradient(600px circle at ${glarePosition.x}% ${glarePosition.y}%, rgba(255,255,255,0.4), transparent 50%)`,
          }}
          aria-hidden="true"
        />
      )}
      <div style={{ transform: "translateZ(20px)", transformStyle: "preserve-3d" }}>
        {children}
      </div>
    </div>
  );
}
