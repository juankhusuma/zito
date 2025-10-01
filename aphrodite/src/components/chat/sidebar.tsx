import supabase from "@/common/supabase"
import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuAction,
    SidebarMenuButton,
    SidebarMenuItem,
    SidebarMenuSkeleton,
    SidebarSeparator,
    SidebarTrigger,
} from "@/components/ui/sidebar"
import { useAuth } from "@/hoc/AuthProvider"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { MessageSquarePlus, MoreHorizontal, Trash2 } from "lucide-react"
import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router"
import PrimaryButton from "../button"
import { cn } from "@/lib/utils"
import { TooltipProvider, TooltipTrigger } from "@radix-ui/react-tooltip"
import { Tooltip, TooltipContent } from "../ui/tooltip"
import { useSessions, Session } from "@/hooks/useSessions"
import { SessionSearch, useSessionSearch } from "./SessionSearch"
import { useQueryClient } from "@tanstack/react-query"

// Sidebar
export function AppSidebar() {
    const { user, loading } = useAuth()
    const navigate = useNavigate()
    const { sessionId } = useParams()
    const [searchQuery, setSearchQuery] = useState("")
    const queryClient = useQueryClient()
    const { sessions, sidebarLoading, groups } = useSessions(user?.id)
    const filteredGroups = useSessionSearch(searchQuery, groups)

    // Redirect kalau user belum login
    useEffect(() => {
        if (!loading && !user) {
            console.log("User not found, redirecting to login")
            window.location.href = "/login?next=/chat"
        }
    }, [user, loading])

    // Render
    return (
        <Sidebar collapsible="offcanvas" className="absolute border-t h-full flex-1 bg-gray-100 shadow-sm z-[50]">
            <TooltipProvider>
                <SidebarHeader className="p-3">
                    <div className="flex flex-col gap-3">
                        <div className="flex items-center justify-between">
                            <SidebarTrigger className="cursor-pointer lg:hidden p-1.5 hover:bg-gray-100 rounded-full transition-colors" />
                        </div>

                        <PrimaryButton
                            className="flex items-center gap-2 justify-center bg-[#192f59] hover:bg-[#0d1e3f] transition-colors py-2.5 rounded-lg text-white shadow-sm"
                            onClick={() => navigate("/chat")}
                        >
                            <MessageSquarePlus size={16} />
                            <span className="text-sm font-medium">New Chat</span>
                        </PrimaryButton>

                        <SessionSearch
                            searchQuery={searchQuery}
                            onSearchChange={setSearchQuery}
                        />
                    </div>
                    <SidebarSeparator className="mt-3" />
                </SidebarHeader>

                <SidebarContent className="px-2">
                    {(sidebarLoading && sessions.length === 0) && (
                        <SidebarMenu>
                            {Array.from({ length: 6 }).map((_, idx) => (
                                <SidebarMenuItem key={idx} className="mb-1">
                                    <SidebarMenuSkeleton className="h-10" />
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    )}

                    {!sidebarLoading && Object.keys(filteredGroups).length === 0 && searchQuery && (
                        <div className="p-4 text-center text-gray-500">
                            <p className="text-sm">No conversations found</p>
                        </div>
                    )}

                    {!sidebarLoading && Object.entries(filteredGroups)
                        .filter(([_, sessions]) => sessions.length > 0)
                        .map(([label, sessions]) => (
                            <SidebarGroup key={label}>
                                <SidebarGroupLabel className="px-3 text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    {label}
                                </SidebarGroupLabel>
                                <SidebarGroupContent>
                                    <SidebarMenu>
                                        {sessions.map((s) => (
                                            <SidebarMenuItem
                                                key={s.id}
                                                className={cn(
                                                    "cursor-pointer group/session rounded-md mb-1 overflow-hidden",
                                                    sessionId === s.id ? "bg-[#192f59]/10" : "hover:bg-gray-100"
                                                )}
                                            >
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <span className="flex-1">
                                                            <SidebarMenuButton asChild>
                                                                <div
                                                                    onClick={() => navigate(s.id)}
                                                                    className={cn(
                                                                        "flex items-center py-2 pl-3 pr-1 text-sm font-medium truncate transition-colors",
                                                                        sessionId === s.id ? "text-[#192f59]" : "text-gray-700"
                                                                    )}
                                                                >
                                                                    <span className="truncate">{s.title}</span>
                                                                </div>
                                                            </SidebarMenuButton>
                                                        </span>
                                                    </TooltipTrigger>
                                                    <TooltipContent side="right">{s.title}</TooltipContent>
                                                </Tooltip>

                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <SidebarMenuAction>
                                                            <div className="p-1.5 hover:bg-gray-200 rounded-full transition-colors">
                                                                <MoreHorizontal className="h-4 w-4 text-gray-500" />
                                                            </div>
                                                        </SidebarMenuAction>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent side="right" align="start" className="w-48">
                                                        <DropdownMenuItem
                                                            onClick={async () => {
                                                                if (!user) return
                                                                const { error } = await supabase.from("session").delete().eq("id", s.id)
                                                                if (error) {
                                                                    console.error("Error deleting session:", error)
                                                                    return
                                                                }
                                                                if (sessionId === s.id) {
                                                                    navigate("/chat")
                                                                }
                                                                queryClient.setQueryData(["sessions", user.id], (oldData: Session[] = []) =>
                                                                    oldData.filter((ss) => ss.id !== s.id)
                                                                )
                                                            }}
                                                            className="text-red-600 cursor-pointer focus:bg-red-50 focus:text-red-700"
                                                        >
                                                            <Trash2 className="h-4 w-4 mr-2" />
                                                            <span>Delete Conversation</span>
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </SidebarMenuItem>
                                        ))}
                                    </SidebarMenu>
                                </SidebarGroupContent>
                            </SidebarGroup>
                        ))}
                </SidebarContent>

                <SidebarFooter className="p-3 border-t">
                    <div className="text-xs text-center text-gray-500">
                        <p>Lexin Chat © {new Date().getFullYear()}</p>
                    </div>
                </SidebarFooter>
            </TooltipProvider>
        </Sidebar>
    )
}