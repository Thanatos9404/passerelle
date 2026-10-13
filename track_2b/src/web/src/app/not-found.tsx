import { ButtonLink } from "@/components/ui/button";
import { Logo } from "@/components/brand/logo";

export default function NotFound() {
  return (
    <main className="grid min-h-dvh place-items-center bg-[linear-gradient(180deg,#B7D5F1_0%,#F4E6DA_100%)] p-6 text-center">
      <div>
        <Logo className="justify-center" />
        <h1 className="t-h2 mt-10">This page took the wrong bridge.</h1>
        <p className="t-lead mt-3">The page you asked for does not exist.</p>
        <div className="mt-8 flex justify-center gap-3">
          <ButtonLink href="/" variant="secondary">Home</ButtonLink>
          <ButtonLink href="/workspace/" arrow>Open workspace</ButtonLink>
        </div>
      </div>
    </main>
  );
}
