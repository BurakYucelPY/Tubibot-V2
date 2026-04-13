import { Button } from "@/components/landing/Button";

export function SignUpForm() {
  return (
    <div className="relative isolate mt-8 flex items-center pr-1">
      <p className="w-0 flex-auto truncate px-4 py-2.5 text-sm/6 text-gray-400">
        TÜBİTAK süreçleri hakkında bilgi edinin
      </p>
      <Button href="/chat" arrow>
        Tübibota Sor
      </Button>
      <div className="absolute inset-0 -z-10 rounded-lg bg-white/2.5 ring-1 ring-white/15" />
    </div>
  );
}
