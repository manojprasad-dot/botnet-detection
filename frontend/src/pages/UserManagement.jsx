import React, { useState, useEffect } from "react";
import {
  Users,
  ShieldCheck,
  Plus,
  Edit2,
  Lock,
  Unlock,
  RefreshCw,
  Search,
} from "lucide-react";
import {
  adminGetUsers,
  adminCreateUser,
  adminEditUser,
  adminUnlockUser,
  adminGetAuditLogs,
} from "../services/api";

export default function UserManagement() {
  const [activeTab, setActiveTab] = useState("users"); // users or audits
  const [usersList, setUsersList] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userError, setUserError] = useState("");

  const [newUser, setNewUser] = useState({
    username: "",
    email: "",
    password: "",
    role: "read_only",
    department: "",
    full_name: "",
  });

  const [editUser, setEditUser] = useState({
    username: "",
    email: "",
    role: "",
    department: "",
    full_name: "",
    phone: "",
    is_active: true,
  });

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === "users") {
        const u = await adminGetUsers();
        setUsersList(u || []);
      } else {
        const a = await adminGetAuditLogs();
        setAuditLogs(a || []);
      }
    } catch (err) {
      console.error("Failed to load admin panel data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setUserError("");
    try {
      await adminCreateUser(newUser);
      setShowAddUserModal(false);
      setNewUser({
        username: "",
        email: "",
        password: "",
        role: "read_only",
        department: "",
        full_name: "",
      });
      loadData();
    } catch (err) {
      setUserError(err.message || "Failed to provision user.");
    }
  };

  const handleEditUserSubmit = async (e) => {
    e.preventDefault();
    setUserError("");
    try {
      await adminEditUser(selectedUser.id, editUser);
      setShowEditUserModal(false);
      setSelectedUser(null);
      loadData();
    } catch (err) {
      setUserError(err.message || "Failed to save user registry changes.");
    }
  };

  const handleOpenEditModal = (user) => {
    setSelectedUser(user);
    setEditUser({
      username: user.username || "",
      email: user.email || "",
      role: user.role || "",
      department: user.department || "",
      full_name: user.full_name || "",
      phone: user.phone || "",
      is_active: user.is_active,
    });
    setShowEditUserModal(true);
  };

  const handleUnlockUser = async (userId) => {
    try {
      await adminUnlockUser(userId);
      alert("User account unlocked successfully.");
      loadData();
    } catch (err) {
      alert("Failed to unlock user: " + err.message);
    }
  };

  const filteredUsers = usersList.filter((u) => {
    const q = searchQuery.toLowerCase();
    return (
      u.username.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      (u.full_name || "").toLowerCase().includes(q) ||
      (u.department || "").toLowerCase().includes(q)
    );
  });

  const filteredAudits = auditLogs.filter((a) => {
    const q = searchQuery.toLowerCase();
    return (
      (a.ip_address || "").includes(q) ||
      (a.status || "").toLowerCase().includes(q) ||
      (a.failure_reason || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="font-orbitron font-black text-lg tracking-[2px] text-white">ACCESS & POLICIES REGISTRY</h2>
          <p className="text-[10px] text-[#5A7090] tracking-[1.5px] uppercase mt-0.5">EDR USER MANAGEMENT</p>
        </div>
        <div className="flex gap-3">
          {activeTab === "users" && (
            <button
              onClick={() => setShowAddUserModal(true)}
              className="px-4 py-2 bg-[#9B59FF] hover:bg-[#9B59FF]/80 text-white font-orbitron text-xs font-bold tracking-wider rounded-lg flex items-center gap-2 cursor-pointer transition-all shadow-lg shadow-purple-500/10"
            >
              <Plus className="h-4 w-4" />
              PROVISION USER
            </button>
          )}
          <button
            onClick={loadData}
            className="p-2 border border-[#1E293B] rounded-lg bg-[#0C1426] hover:bg-[#1E293B] text-white cursor-pointer transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-[#1E293B] pb-px">
        <button
          onClick={() => { setActiveTab("users"); setSearchQuery(""); }}
          className={`flex items-center gap-2 px-6 py-3 border-b-2 font-orbitron text-xs font-bold tracking-wider transition-all cursor-pointer ${
            activeTab === "users"
              ? "border-[#9B59FF] text-white"
              : "border-transparent text-[#5A7090] hover:text-white"
          }`}
        >
          <Users className="h-4.5 w-4.5" />
          ACTIVE USER REGISTRY
        </button>
        <button
          onClick={() => { setActiveTab("audits"); setSearchQuery(""); }}
          className={`flex items-center gap-2 px-6 py-3 border-b-2 font-orbitron text-xs font-bold tracking-wider transition-all cursor-pointer ${
            activeTab === "audits"
              ? "border-[#9B59FF] text-white"
              : "border-transparent text-[#5A7090] hover:text-white"
          }`}
        >
          <ShieldCheck className="h-4.5 w-4.5" />
          ACCESS AUDIT TRAILS
        </button>
      </div>

      {/* Search Filter Toolbar */}
      <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl p-4 flex flex-wrap gap-4 items-center justify-between shadow-lg text-xs">
        <div className="relative w-64">
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-[#5A7090]">
            <Search className="h-4 w-4" />
          </span>
          <input
            type="text"
            placeholder={activeTab === "users" ? "Search operator, department..." : "Search IP, status..."}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg pl-9 pr-4 py-2 text-xs text-white placeholder-[#5A7090] focus:outline-none focus:border-[#9B59FF] transition-all"
          />
        </div>

        <span className="font-orbitron text-[#5A7090]">
          ENTRIES COUNT: <span className="text-[#9B59FF] font-bold">{activeTab === "users" ? filteredUsers.length : filteredAudits.length}</span>
        </span>
      </div>

      {/* Main Grid */}
      <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl overflow-hidden shadow-lg">
        {activeTab === "users" ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#1E293B] bg-[#050A16]/50 text-[#5A7090] font-semibold tracking-wider">
                  <th className="p-4">USERNAME</th>
                  <th className="p-4">FULL NAME</th>
                  <th className="p-4">ROLE</th>
                  <th className="p-4">DEPARTMENT</th>
                  <th className="p-4">LOCKOUT STATE</th>
                  <th className="p-4">REGISTRY ACTIONS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E293B] text-white">
                {filteredUsers.length > 0 ? (
                  filteredUsers.map((u) => (
                    <tr key={u.id} className="hover:bg-[#1E293B]/20">
                      <td className="p-4 font-bold text-white">
                        <div className="flex flex-col">
                          <span>{u.username}</span>
                          <span className="text-[10px] text-[#5A7090] font-mono mt-0.5">{u.email}</span>
                        </div>
                      </td>
                      <td className="p-4">{u.full_name || "N/A"}</td>
                      <td className="p-4 uppercase font-bold font-orbitron text-[#00D4FF]">
                        {u.role.replace("super_", "").replace("_", " ")}
                      </td>
                      <td className="p-4 text-[#C5D0E6]">{u.department || "N/A"}</td>
                      <td className="p-4">
                        {u.locked_until && new Date(u.locked_until) > new Date() ? (
                          <span className="text-[#FF355E] font-bold font-orbitron flex items-center gap-1.5 animate-pulse">
                            <Lock className="h-3.5 w-3.5" />
                            LOCKED
                          </span>
                        ) : (
                          <span className="text-[#00E676] font-bold font-orbitron flex items-center gap-1.5">
                            <Unlock className="h-3.5 w-3.5" />
                            ACTIVE
                          </span>
                        )}
                      </td>
                      <td className="p-4">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleOpenEditModal(u)}
                            className="p-1.5 border border-[#1E293B] rounded bg-[#060B18] hover:bg-[#1E293B] text-white cursor-pointer"
                            title="Edit User Registry"
                          >
                            <Edit2 className="h-3.5 w-3.5" />
                          </button>
                          {u.locked_until && new Date(u.locked_until) > new Date() && (
                            <button
                              onClick={() => handleUnlockUser(u.id)}
                              className="p-1.5 border border-emerald-500/30 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-[#00E676] cursor-pointer"
                              title="Unlock User"
                            >
                              <Unlock className="h-3.5 w-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="p-8 text-center text-[#5A7090] text-sm">
                      No user accounts found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#1E293B] bg-[#050A16]/50 text-[#5A7090] font-semibold tracking-wider">
                  <th className="p-4">LOGIN TIME</th>
                  <th className="p-4">IP ADDRESS</th>
                  <th className="p-4">BROWSER / OS</th>
                  <th className="p-4">STATE</th>
                  <th className="p-4">FAILURE EXPLANATION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E293B] text-white">
                {filteredAudits.length > 0 ? (
                  filteredAudits.map((a) => (
                    <tr key={a.id} className="hover:bg-[#1E293B]/20">
                      <td className="p-4 text-[#C5D0E6]">{new Date(a.login_time).toLocaleString()}</td>
                      <td className="p-4 font-mono">{a.ip_address}</td>
                      <td className="p-4 text-[#5A7090]">
                        {a.browser} on {a.operating_system}
                      </td>
                      <td className="p-4">
                        <span className={`font-orbitron font-bold text-[10px] ${
                          a.status === "success"
                            ? "text-[#00E676]"
                            : a.status === "locked"
                            ? "text-[#9B59FF] animate-pulse"
                            : "text-[#FF355E]"
                        }`}>
                          {a.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-4 text-[#5A7090] font-mono text-[10px]">
                        {a.failure_reason || "None"}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="p-8 text-center text-[#5A7090] text-sm">
                      No login audit histories recorded.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Provision User Modal */}
      {showAddUserModal && (
        <div className="fixed inset-0 bg-[#060B18]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl w-full max-w-md p-6 relative shadow-2xl">
            <span className="font-orbitron text-xs font-black text-white tracking-[2px] border-b border-[#1E293B] pb-2.5 mb-4 block">
              PROVISION NEW EDR OPERATOR
            </span>

            {userError && (
              <div className="p-3 bg-rose-950/20 border border-rose-500/30 rounded-lg text-xs text-rose-400 mb-4">
                {userError}
              </div>
            )}

            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">USERNAME</label>
                <input
                  type="text"
                  required
                  value={newUser.username}
                  onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                  placeholder="e.g. jdoe"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">EMAIL ADDRESS</label>
                <input
                  type="email"
                  required
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                  placeholder="e.g. operator@kovirx.com"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">INITIAL PASSWORD</label>
                <input
                  type="password"
                  required
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                  placeholder="Minimum 12 chars..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">ACCESS ROLE</label>
                  <select
                    value={newUser.role}
                    onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                    className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                  >
                    <option value="super_admin">Super Admin</option>
                    <option value="soc_manager">SOC Manager</option>
                    <option value="soc_analyst">SOC Analyst</option>
                    <option value="incident_responder">Incident Responder</option>
                    <option value="read_only">Read Only</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">DEPARTMENT</label>
                  <input
                    type="text"
                    value={newUser.department}
                    onChange={(e) => setNewUser({ ...newUser, department: e.target.value })}
                    className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                    placeholder="e.g. Tier 1"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">FULL NAME</label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                  placeholder="e.g. John Doe"
                />
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddUserModal(false)}
                  className="px-4 py-2 border border-[#1E293B] rounded-lg text-xs font-bold text-white font-orbitron hover:bg-[#1E293B]"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#9B59FF] hover:bg-[#9B59FF]/85 rounded-lg text-xs font-bold text-white font-orbitron"
                >
                  PROVISION AGENT
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {showEditUserModal && (
        <div className="fixed inset-0 bg-[#060B18]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0C1426] border border-[#1E293B] rounded-xl w-full max-w-md p-6 relative shadow-2xl">
            <span className="font-orbitron text-xs font-black text-white tracking-[2px] border-b border-[#1E293B] pb-2.5 mb-4 block">
              EDIT OPERATOR REGISTRY
            </span>

            {userError && (
              <div className="p-3 bg-rose-950/20 border border-rose-500/30 rounded-lg text-xs text-rose-400 mb-4">
                {userError}
              </div>
            )}

            <form onSubmit={handleEditUserSubmit} className="space-y-4">
              <div>
                <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">USERNAME</label>
                <input
                  type="text"
                  required
                  value={editUser.username}
                  onChange={(e) => setEditUser({ ...editUser, username: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                />
              </div>

              <div>
                <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">EMAIL ADDRESS</label>
                <input
                  type="email"
                  required
                  value={editUser.email}
                  onChange={(e) => setEditUser({ ...editUser, email: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">ACCESS ROLE</label>
                  <select
                    value={editUser.role}
                    onChange={(e) => setEditUser({ ...editUser, role: e.target.value })}
                    className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                  >
                    <option value="super_admin">Super Admin</option>
                    <option value="soc_manager">SOC Manager</option>
                    <option value="soc_analyst">SOC Analyst</option>
                    <option value="incident_responder">Incident Responder</option>
                    <option value="read_only">Read Only</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">DEPARTMENT</label>
                  <input
                    type="text"
                    value={editUser.department}
                    onChange={(e) => setEditUser({ ...editUser, department: e.target.value })}
                    className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-[#5A7090] font-orbitron block mb-1">FULL NAME</label>
                <input
                  type="text"
                  value={editUser.full_name}
                  onChange={(e) => setEditUser({ ...editUser, full_name: e.target.value })}
                  className="w-full bg-[#060B18] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none"
                />
              </div>

              <div className="flex items-center gap-2 border-t border-[#1E293B]/50 pt-3">
                <input
                  type="checkbox"
                  id="user_is_active"
                  checked={editUser.is_active}
                  onChange={(e) => setEditUser({ ...editUser, is_active: e.target.checked })}
                  className="accent-[#9B59FF] cursor-pointer"
                />
                <label htmlFor="user_is_active" className="text-xs text-white font-bold cursor-pointer font-orbitron">
                  ACCOUNT IS ACTIVE
                </label>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => { setShowEditUserModal(false); setSelectedUser(null); }}
                  className="px-4 py-2 border border-[#1E293B] rounded-lg text-xs font-bold text-white font-orbitron hover:bg-[#1E293B]"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#9B59FF] hover:bg-[#9B59FF]/85 rounded-lg text-xs font-bold text-white font-orbitron"
                >
                  SAVE CHANGES
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
