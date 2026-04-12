import { useId } from "react";

import { Button } from "@/components/landing/Button";

export function SignUpForm() {
  const id = useId();

  return (
    <div className="relative isolate mt-8 flex items-center pr-1">
      <label htmlFor={id} className="sr-only">
        Email address
      </label>
      <input
        type="email"
        autoComplete="email"
        name="email"
        id={id}
        placeholder="Email address"
        className="peer w-0 flex-auto bg-transparent px-4 py-2.5 text-base text-white placeholder:text-gray-500 focus:outline-hidden sm:text-[0.8125rem]/6"
      />
      <Button href="/chat" arrow>
        Get updates
      </Button>
      <div className="absolute inset-0 -z-10 rounded-lg transition peer-focus:ring-4 peer-focus:ring-red-400/15" />
      <div className="absolute inset-0 -z-10 rounded-lg bg-white/2.5 ring-1 ring-white/15 transition peer-focus:ring-red-400" />
    </div>
  );
}
