import { useAuth } from "@/auth/AuthProvider";
import { API_BASE_URL } from "@/lib/api";
import { formatWindow, labelForRole } from "@/lib/labels";

export default function Settings() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <div className="px-4 py-5 md:px-7">
      <div className="max-w-xl">
        <h2 className="mb-5 text-lg font-bold">Settings</h2>
        <section className="mb-6 overflow-hidden rounded-xl border border-[#e7e1d8] bg-white">
          <div className="border-b border-[#f0ede8] px-5 py-4">
            <p className="text-xs font-semibold text-[#6b6b6b]">Profile</p>
          </div>
          <dl>
            <div className="flex items-center justify-between border-b border-[#f0ede8] px-5 py-4">
              <dt className="text-sm text-[#555]">Full name</dt>
              <dd className="text-sm font-semibold">{user.full_name}</dd>
            </div>
            <div className="flex items-center justify-between border-b border-[#f0ede8] px-5 py-4">
              <dt className="text-sm text-[#555]">Email</dt>
              <dd className="text-sm font-semibold">{user.email}</dd>
            </div>
            <div className="flex items-center justify-between border-b border-[#f0ede8] px-5 py-4">
              <dt className="text-sm text-[#555]">Role</dt>
              <dd className="text-sm font-semibold">{labelForRole(user.role)}</dd>
            </div>
            <div className="flex items-center justify-between px-5 py-4">
              <dt className="text-sm text-[#555]">Created</dt>
              <dd className="font-mono text-xs">{formatWindow(user.created_at)}</dd>
            </div>
          </dl>
        </section>

        <section className="overflow-hidden rounded-xl border border-[#e7e1d8] bg-white">
          <div className="border-b border-[#f0ede8] px-5 py-4">
            <p className="text-xs font-semibold text-[#6b6b6b]">API connection</p>
          </div>
          <div className="px-5 py-4">
            <p className="text-sm text-[#555]">Base URL</p>
            <code className="mt-1 block font-mono text-xs">{API_BASE_URL}</code>
            <p className="mt-2 text-xs leading-relaxed text-[#6b6b6b]">
              Change <span className="font-mono">VITE_API_BASE_URL</span> to point at the live server. Tokens stay in session storage and are sent as Bearer JWTs.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
