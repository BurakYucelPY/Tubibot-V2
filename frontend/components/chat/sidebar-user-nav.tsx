"use client";

import { ChevronUp, HomeIcon, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import type { User } from "next-auth";
import { signOut, useSession } from "next-auth/react";
import { useState } from "react";
import { useSWRConfig } from "swr";
import { unstable_serialize } from "swr/infinite";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { guestRegex } from "@/lib/constants";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { getChatHistoryPaginationKey } from "./sidebar-history";
import { LoaderIcon } from "./icons";
import { toast } from "./toast";

function emailToHue(email: string): number {
  let hash = 0;
  for (const char of email) {
    hash = char.charCodeAt(0) + ((hash << 5) - hash);
  }
  return Math.abs(hash) % 360;
}

export function SidebarUserNav({ user }: { user: User }) {
  const router = useRouter();
  const { data, status } = useSession();
  const { mutate } = useSWRConfig();
  const [showDeleteAllDialog, setShowDeleteAllDialog] = useState(false);

  const isGuest = guestRegex.test(data?.user?.email ?? "");

  const handleDeleteAll = () => {
    setShowDeleteAllDialog(false);
    mutate(unstable_serialize(getChatHistoryPaginationKey), [], {
      revalidate: false,
    });
    fetch(`${process.env.NEXT_PUBLIC_BASE_PATH ?? ""}/api/history`, {
      method: "DELETE",
    });
    toast({ type: "success", description: "Tüm sohbetler silindi" });
  };

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            {status === "loading" ? (
              <SidebarMenuButton className="h-10 justify-between rounded-lg bg-transparent text-sidebar-foreground/50 transition-colors duration-150 data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground">
                <div className="flex flex-row items-center gap-2">
                  <div className="size-6 animate-pulse rounded-full bg-sidebar-foreground/10" />
                  <span className="animate-pulse rounded-md bg-sidebar-foreground/10 text-transparent text-[13px]">
                    Yükleniyor...
                  </span>
                </div>
                <div className="animate-spin text-sidebar-foreground/50">
                  <LoaderIcon />
                </div>
              </SidebarMenuButton>
            ) : (
              <SidebarMenuButton
                className="h-8 px-2 rounded-lg bg-transparent text-sidebar-foreground/70 transition-colors duration-150 hover:text-sidebar-foreground data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                data-testid="user-nav-button"
              >
                <div
                  className="size-5 shrink-0 rounded-full ring-1 ring-sidebar-border/50"
                  style={{
                    background: `linear-gradient(135deg, oklch(0.35 0.08 ${emailToHue(user.email ?? "")}), oklch(0.25 0.05 ${emailToHue(user.email ?? "") + 40}))`,
                  }}
                />
                <span className="truncate text-[13px]" data-testid="user-email">
                  {isGuest ? "Misafir" : user?.email}
                </span>
                <ChevronUp className="ml-auto size-3.5 text-sidebar-foreground/50" />
              </SidebarMenuButton>
            )}
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="w-(--radix-popper-anchor-width) rounded-lg border border-border/60 bg-card/95 backdrop-blur-xl shadow-[var(--shadow-float)]"
            data-testid="user-nav-menu"
            side="top"
          >
            <DropdownMenuItem asChild data-testid="user-nav-item-home">
              <button
                className="flex w-full cursor-pointer items-center gap-2 text-[13px]"
                onClick={() => router.push("/")}
                type="button"
              >
                <HomeIcon className="size-3.5 shrink-0" />
                Anasayfaya dön
              </button>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {!isGuest && (
              <>
                <DropdownMenuItem
                  asChild
                  data-testid="user-nav-item-delete-all"
                >
                  <button
                    className="flex w-full cursor-pointer items-center gap-2 text-[13px] text-destructive/70 hover:text-destructive focus:text-destructive"
                    onClick={() => setShowDeleteAllDialog(true)}
                    type="button"
                  >
                    <Trash2 className="size-3.5 shrink-0" />
                    Tümünü sil
                  </button>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
              </>
            )}
            <DropdownMenuItem asChild data-testid="user-nav-item-auth">
              <button
                className="w-full cursor-pointer text-[13px]"
                onClick={() => {
                  if (status === "loading") {
                    toast({
                      type: "error",
                      description:
                        "Kimlik doğrulama durumu kontrol ediliyor, lütfen tekrar deneyin!",
                    });

                    return;
                  }

                  if (isGuest) {
                    router.push("/login");
                  } else {
                    signOut({
                      redirectTo: "/",
                    });
                  }
                }}
                type="button"
              >
                {isGuest ? "Hesabınıza giriş yapın" : "Çıkış yap"}
              </button>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>

    <AlertDialog onOpenChange={setShowDeleteAllDialog} open={showDeleteAllDialog}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Tüm sohbetler silinsin mi?</AlertDialogTitle>
          <AlertDialogDescription>
            Bu işlem geri alınamaz. Tüm sohbetleriniz kalıcı olarak
            silinecek ve sunucularımızdan kaldırılacak.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Vazgeç</AlertDialogCancel>
          <AlertDialogAction onClick={handleDeleteAll}>
            Tümünü Sil
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
    </>
  );
}
