export function Logo({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`inline-flex items-center gap-x-1 ${className ?? ""}`}
      {...props}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/logoTubi-Photoroom.webp"
        alt="Tübibot"
        className="h-8 w-auto flex-none"
      />
      <span
        className="text-[28px]"
        style={{
          fontFamily: "Avillia, system-ui, sans-serif",
          letterSpacing: "0.01em",
          background: "linear-gradient(to right, #5BAEE8, #ffffff)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
        }}
      >
        Tübibot
      </span>
    </div>
  );
}
