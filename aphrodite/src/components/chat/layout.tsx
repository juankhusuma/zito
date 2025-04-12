import { SidebarProvider, SidebarTrigger } from "../ui/sidebar";
import { AppSidebar } from "./sidebar";
import { Outlet } from "react-router";

export default function ChatLayout() {
    return (
        <SidebarProvider>
            <AppSidebar />
            <main className="flex w-full border-t flex-col">
                <SidebarTrigger />
                <Outlet />
            </main>
        </SidebarProvider>
    )
}