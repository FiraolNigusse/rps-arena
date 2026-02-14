import { createContext, useContext, useState } from "react";

const UserContext = createContext(null);

export function UserProvider({ children, initialUser }) {
  const [user, setUser] = useState(initialUser);

  const updateUser = (updates) => {
    setUser((prev) => (prev ? { ...prev, ...updates } : prev));
  };

  return (
    <UserContext.Provider value={{ user, setUser, updateUser }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within UserProvider");
  return ctx;
}
