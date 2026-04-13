const dateFormatter = new Intl.DateTimeFormat("tr-TR", {
  year: "numeric",
  month: "short",
  day: "numeric",
  timeZone: "UTC",
});

export function FormattedDate({
  date,
  ...props
}: React.ComponentPropsWithoutRef<"time"> & { date: string | Date }) {
  const parsed = typeof date === "string" ? new Date(date) : date;

  return (
    <time dateTime={parsed.toISOString()} {...props}>
      {dateFormatter.format(parsed)}
    </time>
  );
}
