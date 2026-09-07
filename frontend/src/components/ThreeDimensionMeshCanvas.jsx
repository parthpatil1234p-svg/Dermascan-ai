import { useEffect, useRef } from "react";

/**
 * ThreeDimensionMeshCanvas - Hardware-accelerated 60 FPS HTML5 Canvas
 * Renders an interactive 3D particle constellation & biometric wireframe mesh
 * with true 3D perspective projection math:
 *   ScreenX = X * (Focal / (Focal + Z)) + CenterX
 *   ScreenY = Y * (Focal / (Focal + Z)) + CenterY
 */
export default function ThreeDimensionMeshCanvas({
  className = "",
  mode = "ambient", // "ambient" | "hero" | "scanner"
  nodeCount = 45,
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId;
    let width = (canvas.width = canvas.offsetWidth * window.devicePixelRatio || 800);
    let height = (canvas.height = canvas.offsetHeight * window.devicePixelRatio || 600);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth * window.devicePixelRatio || 800;
      height = canvas.height = canvas.offsetHeight * window.devicePixelRatio || 600;
    };

    window.addEventListener("resize", handleResize);

    // Mouse tracking for 3D parallax tilt
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      const nx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const ny = ((e.clientY - rect.top) / rect.height) * 2 - 1;
      mouse.targetX = nx * 0.4;
      mouse.targetY = ny * 0.4;
    };

    window.addEventListener("mousemove", handleMouseMove);

    // Generate 3D point cloud
    const points = [];
    const count = mode === "hero" ? 55 : nodeCount;
    const radius = Math.min(width, height) * 0.28;

    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      const r = radius * (0.6 + Math.random() * 0.4);

      points.push({
        x: r * Math.sin(phi) * Math.cos(theta),
        y: r * Math.sin(phi) * Math.sin(theta) * 1.15,
        z: r * Math.cos(phi),
        origX: r * Math.sin(phi) * Math.cos(theta),
        origY: r * Math.sin(phi) * Math.sin(theta) * 1.15,
        origZ: r * Math.cos(phi),
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        vz: (Math.random() - 0.5) * 0.3,
        size: Math.random() * 2.2 + 1.2,
        pulse: Math.random() * Math.PI * 2,
        color: Math.random() > 0.4 ? "emerald" : Math.random() > 0.5 ? "cyan" : "violet",
      });
    }

    let angleY = 0;
    let angleX = 0;
    const focalLength = 360;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Smooth mouse interpolation
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      angleY += 0.003 + mouse.x * 0.01;
      angleX = mouse.y * 0.3;

      const cosY = Math.cos(angleY);
      const sinY = Math.sin(angleY);
      const cosX = Math.cos(angleX);
      const sinX = Math.sin(angleX);

      const centerX = width / 2;
      const centerY = height / 2;

      // Draw subtle background radial glow
      const grad = ctx.createRadialGradient(
        centerX,
        centerY,
        10,
        centerX,
        centerY,
        radius * 1.4
      );
      grad.addColorStop(0, "rgba(16, 185, 129, 0.06)");
      grad.addColorStop(0.5, "rgba(6, 182, 212, 0.03)");
      grad.addColorStop(1, "rgba(0, 0, 0, 0)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, width, height);

      // Project 3D points to 2D
      const projected = [];

      for (let i = 0; i < points.length; i++) {
        const p = points[i];
        p.pulse += 0.03;

        // Rotation around Y then X
        const x1 = p.x * cosY - p.z * sinY;
        const z1 = p.z * cosY + p.x * sinY;

        const y2 = p.y * cosX - z1 * sinX;
        const z2 = z1 * cosX + p.y * sinX + 450;

        if (z2 > 10) {
          const scale = focalLength / z2;
          const sx = x1 * scale + centerX;
          const sy = y2 * scale + centerY;
          const alpha = Math.max(0.1, Math.min(1, (z2 - 100) / 450));

          projected.push({
            sx,
            sy,
            z: z2,
            scale,
            alpha,
            size: p.size * scale * (1 + Math.sin(p.pulse) * 0.25),
            color: p.color,
          });
        }
      }

      projected.sort((a, b) => b.z - a.z);

      // Draw connecting wireframe lines between close nodes
      ctx.lineWidth = 0.75;
      for (let i = 0; i < projected.length; i++) {
        for (let j = i + 1; j < projected.length; j++) {
          const p1 = projected[i];
          const p2 = projected[j];
          const dx = p1.sx - p2.sx;
          const dy = p1.sy - p2.sy;
          const dist = Math.sqrt(dx * dx + dy * dy);

          const maxDist = 70 * ((p1.scale + p2.scale) / 2);

          if (dist < maxDist) {
            const lineAlpha = (1 - dist / maxDist) * 0.22 * Math.min(p1.alpha, p2.alpha);
            ctx.strokeStyle =
              p1.color === "emerald"
                ? `rgba(16, 185, 129, ${lineAlpha})`
                : p1.color === "cyan"
                ? `rgba(6, 182, 212, ${lineAlpha})`
                : `rgba(167, 139, 250, ${lineAlpha})`;
            ctx.beginPath();
            ctx.moveTo(p1.sx, p1.sy);
            ctx.lineTo(p2.sx, p2.sy);
            ctx.stroke();
          }
        }
      }

      // Draw projected nodes with glow
      for (let i = 0; i < projected.length; i++) {
        const p = projected[i];
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, Math.max(1, p.size), 0, Math.PI * 2);

        if (p.color === "emerald") {
          ctx.fillStyle = `rgba(52, 211, 153, ${p.alpha * 0.9})`;
          ctx.shadowColor = "rgba(16, 185, 129, 0.8)";
        } else if (p.color === "cyan") {
          ctx.fillStyle = `rgba(103, 232, 249, ${p.alpha * 0.9})`;
          ctx.shadowColor = "rgba(6, 182, 212, 0.8)";
        } else {
          ctx.fillStyle = `rgba(196, 181, 253, ${p.alpha * 0.85})`;
          ctx.shadowColor = "rgba(139, 92, 246, 0.7)";
        }

        ctx.shadowBlur = 6 * p.scale;
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, [mode, nodeCount]);

  return (
    <canvas
      ref={canvasRef}
      className={`pointer-events-none absolute inset-0 h-full w-full ${className}`}
      aria-hidden="true"
    />
  );
}
