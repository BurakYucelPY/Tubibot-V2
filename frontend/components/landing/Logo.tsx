export function Logo({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`inline-flex items-center gap-x-2 ${className ?? ""}`}
      {...props}
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/TubibotIcon.svg"
        alt="Tübibot"
        className="h-8 w-auto flex-none"
      />
      <span
        className="font-semibold text-[20px] tracking-tight text-white"
        style={{
          fontFamily: "var(--font-mona-sans), system-ui, sans-serif",
          letterSpacing: "-0.02em",
        }}
      >
        Tübibot
      </span>
    </div>
  );
}
