import Link from "next/link";

import { IconLink } from "@/components/landing/IconLink";
import { Logo } from "@/components/landing/Logo";
import { SignUpForm } from "@/components/landing/SignUpForm";

function TubitakIcon(props: React.ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 111.45 93.07" aria-hidden="true" {...props}>
      <path fill="#fff" d="M75.99,27.97h-2.36c0,3.08-.78,5.97-2.14,8.5.46.84.84,1.73,1.16,2.65,2.11-3.2,3.34-7.03,3.34-11.14Z"/>
      <path fill="#fff" d="M39.96,36.47c-1.37-2.53-2.14-5.42-2.14-8.5h-2.36c0,4.12,1.23,7.95,3.34,11.14.32-.92.71-1.8,1.16-2.65Z"/>
      <path fill="#fff" d="M73.44,47.55c5.33-4.83,8.68-11.81,8.68-19.57h-3.46c0,5.52-1.95,10.59-5.2,14.55.11.8.17,1.62.17,2.45,0,.88-.07,1.74-.19,2.58Z"/>
      <path fill="#fff" d="M38.01,47.54c-.12-.84-.19-1.7-.19-2.58,0-.83.06-1.65.17-2.45-3.25-3.96-5.2-9.02-5.2-14.55h-3.46c0,7.76,3.35,14.74,8.68,19.57Z"/>
      <path fill="#fff" d="M83.7,27.97c0,8.98-4.23,16.97-10.81,22.09-2.2,7.41-9.05,12.81-17.16,12.81s-14.97-5.4-17.16-12.81c-6.58-5.12-10.81-13.11-10.81-22.09H9.08l46.64,65.1L102.36,27.97h-18.67Z"/>
      <path fill="#ed1c24" d="M27.75,27.97C27.75,12.52,40.27,0,55.72,0s27.97,12.52,27.97,27.97h-1.57c0-14.58-11.82-26.4-26.4-26.4s-26.4,11.82-26.4,26.4h-1.57Z"/>
      <path fill="#ed1c24" d="M32.79,27.97c0-12.67,10.27-22.94,22.94-22.94s22.94,10.27,22.94,22.94h-2.67c0-11.19-9.07-20.26-20.26-20.26s-20.26,9.07-20.26,20.26h-2.67Z"/>
      <path fill="#ed1c24" d="M55.72,48.24c-7.07,0-13.3-3.63-16.93-9.12-.38,1.09-.65,2.23-.81,3.4,4.21,5.12,10.59,8.39,17.74,8.39s13.53-3.27,17.74-8.39c-.16-1.17-.43-2.31-.81-3.4-3.62,5.49-9.85,9.12-16.93,9.12Z"/>
      <path fill="#ed1c24" d="M39.96,36.47c3.03,5.6,8.95,9.41,15.76,9.41s12.74-3.81,15.76-9.41c-2.15-3.98-5.76-7.05-10.11-8.5h12.25c0-9.89-8.02-17.9-17.9-17.9s-17.9,8.02-17.9,17.9h12.25c-4.35,1.45-7.96,4.52-10.11,8.5Z"/>
      <path fill="#ed1c24" d="M38,47.54c.12.86.31,1.7.55,2.52,4.74,3.69,10.7,5.89,17.17,5.89s12.43-2.2,17.17-5.89c.24-.82.43-1.66.55-2.52-4.68,4.24-10.9,6.83-17.72,6.83s-13.04-2.59-17.72-6.83Z"/>
    </svg>
  );
}

export function Intro() {
  return (
    <>
      <div>
        <Link href="/">
          <Logo className="inline-block h-8 w-auto" />
        </Link>
      </div>
      <h1 className="mt-14 font-display text-4xl/tight font-light text-white">
        Yapay zeka destekli{" "}
        <span className="text-red-400">TÜBİTAK araştırma asistanı</span>
      </h1>
      <p className="mt-4 text-sm/6 text-gray-300">
        Tübibot, TÜBİTAK proje başvuru süreçlerinizde size yardımcı olan yapay
        zeka destekli bir araştırma asistanıdır. Sorularınızı sorun, anında
        yanıt alın.
      </p>
      <SignUpForm />
      <div className="mt-8 flex flex-wrap justify-center gap-x-1 gap-y-3 sm:gap-x-2 lg:justify-start">
        <IconLink href="https://arbis.tubitak.gov.tr/" target="_blank" rel="noopener noreferrer" icon={TubitakIcon} className="flex-none">
          ARBİS
        </IconLink>
        <IconLink href="https://ardeb-pbs.tubitak.gov.tr/" target="_blank" rel="noopener noreferrer" icon={TubitakIcon} className="flex-none">
          ARDEB PBS
        </IconLink>
        <IconLink href="https://eteydeb.tubitak.gov.tr/teydebanasayfa.htm" target="_blank" rel="noopener noreferrer" icon={TubitakIcon} className="flex-none">
          TEYDEB
        </IconLink>
        <IconLink href="https://ebideb.tubitak.gov.tr/giris.htm" target="_blank" rel="noopener noreferrer" icon={TubitakIcon} className="flex-none">
          E-BİDEB
        </IconLink>
        <IconLink href="https://bilimtoplum-pbs.tubitak.gov.tr/" target="_blank" rel="noopener noreferrer" icon={TubitakIcon} className="flex-none">
          BİTO
        </IconLink>
        <IconLink href="https://uidb-pbs.tubitak.gov.tr/" target="_blank" rel="noopener noreferrer" icon={TubitakIcon} className="flex-none">
          UİDB
        </IconLink>
        <IconLink href="https://tybsng.tubitak.gov.tr" target="_blank" rel="noopener noreferrer" icon={TubitakIcon} className="flex-none">
          TYBS
        </IconLink>
      </div>
    </>
  );
}

export function IntroFooter() {
  return (
    <p className="flex items-center gap-x-2 text-[1.1rem]/7 text-gray-500">
      Destekleyen{" "}
      <Link
        href="https://www.tubitak.gov.tr"
        target="_blank"
        rel="noopener noreferrer"
        className="group flex items-center gap-x-1.5 transition-colors hover:text-red-400"
      >
        <TubitakIcon className="h-6 w-6 flex-none" />
        <span className="font-medium text-white group-hover:text-red-400">
          TÜBİTAK
        </span>
      </Link>
    </p>
  );
}
