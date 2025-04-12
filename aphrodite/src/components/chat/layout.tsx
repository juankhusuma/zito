import { SidebarProvider, SidebarTrigger } from "../ui/sidebar";
import { AppSidebar } from "./sidebar";
import { Outlet } from "react-router";

export default function ChatLayout() {
    return (
        <div className="relative h-[calc(100svh-16rem)]">
            <SidebarProvider>
                <AppSidebar />
                <main className="absolute flex w-full border-t flex-col">
                    <SidebarTrigger className="mt-5 cursor-pointer ml-2" />
                    <div className="w-full h-[calc(100svh-16rem)] relative">
                        <Outlet />
                    </div>
                </main>
            </SidebarProvider>
        </div>
    )
}