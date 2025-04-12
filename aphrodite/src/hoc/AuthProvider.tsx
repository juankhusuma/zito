import React, { createContext } from "react";
import supabase from "../common/supabase";
import { User } from "@supabase/supabase-js";


interface AuthContextType {
    user: User | null;
    loading: boolean;
    setLoading: React.Dispatch<React.SetStateAction<boolean>>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    setLoading: () => { },
})

export function useAuth() {
    const context = React.useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const [user, setUser] = React.useState<any>(null)
    const [loading, setLoading] = React.useState(true)

    React.useEffect(() => {
        const { data: authListener } = supabase.auth.onAuthStateChange(async (_, session) => {
            setUser(session?.user ?? null)
            setLoading(false)
        })

        return () => {
            authListener.subscription.unsubscribe()
        }
    }, [])

    return (
        <AuthContext.Provider value={{ user, loading, setLoading }}>
            {children}
        </AuthContext.Provider>
    )
}