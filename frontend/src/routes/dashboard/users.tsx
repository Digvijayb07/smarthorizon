import { createFileRoute } from "@tanstack/react-router";
import { Users, UserPlus, Shield, CheckCircle2, MoreHorizontal } from "lucide-react";
import { DashboardLayout } from "@/components/dashboard/DashboardLayout";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/dashboard/users")({
  component: UsersPage,
});

const userList = [
  { id: "usr-1", name: "Alex Chen", email: "alex.chen@smarthorizon.ai", role: "administrator", status: "Active", lastActive: "15m ago" },
  { id: "usr-2", name: "Sarah Chen", email: "sarah.chen@smarthorizon.ai", role: "manager", status: "Active", lastActive: "45m ago" },
  { id: "usr-3", name: "Marcus Johnson", email: "marcus.johnson@smarthorizon.ai", role: "investigator", status: "Active", lastActive: "2h ago" },
  { id: "usr-4", name: "Priya Patel", email: "priya.patel@smarthorizon.ai", role: "investigator", status: "Active", lastActive: "3h ago" },
  { id: "usr-5", name: "David Rodriguez", email: "david.rodriguez@smarthorizon.ai", role: "manager", status: "Inactive", lastActive: "1d ago" },
];

function UsersPage() {
  return (
    <DashboardLayout title="User Management & Directory">
      <div className="space-y-6">
        <div className="rounded-2xl border border-border bg-card p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl bg-violet/10 text-violet">
              <Users className="size-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">Platform User Directory</h2>
              <p className="text-xs text-muted-foreground">Manage user accounts, roles, workspace permissions, and analyst credentials.</p>
            </div>
          </div>
          <Button size="sm" className="gap-2">
            <UserPlus className="size-4" />
            Add New User
          </Button>
        </div>

        <div className="rounded-2xl border border-border bg-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/30 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <th className="px-6 py-4 text-left">User</th>
                  <th className="px-6 py-4 text-left">Assigned Role</th>
                  <th className="px-6 py-4 text-left">Status</th>
                  <th className="px-6 py-4 text-left">Last Active</th>
                  <th className="px-6 py-4 text-left">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {userList.map((user) => (
                  <tr key={user.id} className="hover:bg-muted/20 transition-colors">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-semibold text-foreground">{user.name}</p>
                        <p className="text-xs text-muted-foreground">{user.email}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-violet/10 text-violet capitalize">
                        {user.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-teal/10 text-teal">
                        <CheckCircle2 className="size-3" />
                        {user.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-muted-foreground">{user.lastActive}</td>
                    <td className="px-6 py-4">
                      <Button size="sm" variant="ghost" className="text-xs">
                        <MoreHorizontal className="size-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
