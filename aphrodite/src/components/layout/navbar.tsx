import { Sheet, SheetTrigger, SheetContent } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Icon } from "@iconify/react/dist/iconify.js";
import { useAuth } from "@/hoc/AuthProvider";
import { Skeleton } from "../ui/skeleton";
import supabase from "@/common/supabase";

export default function Navbar() {
    return (
        <div>
            <div className="flex justify-end px-8 xl:px-32 bg-[#192f59]">
                <p className="bg-[#d61b23] text-white text-lg h-full flex py-3 xl:py-5 px-8 font-bold">Faculty of Computer Science</p>
            </div>
            <header className="flex sticky top-0 w-full shrink-0 items-center md:px-6 text-[#163269]">
                <Sheet>
                    <SheetTrigger asChild>
                        <div className="flex items-center gap-6 py-8">
                            <Button variant="outline" size="icon" className="lg:hidden">
                                <MenuIcon className="h-6 w-6" />
                                <span className="sr-only">Toggle navigation menu</span>
                            </Button>
                            <a href="/" className="mr-6 lg:hidden w-full flex justify-center items-center flex-1">
                                <img src="/logo-lexin.png" alt="lexin" width="300px" height="80px" />
                            </a>
                        </div>
                    </SheetTrigger>
                    <SheetContent side="left">
                        <div className="grid gap-2 py-2">
                            <a href="#" className="text-[#163269] flex w-full items-center py-2 text-lg font-semibold">
                                Home
                            </a>
                            <a href="#" className="text-[#163269] flex w-full items-center py-2 text-lg font-semibold">
                                About
                            </a>
                            <a href="#" className="text-[#163269] flex w-full items-center py-2 text-lg font-semibold">
                                Services
                            </a>
                            <a href="#" className="text-[#163269] flex w-full items-center py-2 text-lg font-semibold">
                                Contact
                            </a>
                        </div>
                    </SheetContent>
                </Sheet>
                <div className="relative flex-1">
                    <a href="/" className="hidden lg:flex xl:ml-32 ml-8">
                        <img src="/logo-lexin.png" alt="lexin" width="400px" height="113px" />
                    </a>
                </div>
                <nav className="ml-auto hidden lg:flex my-16 flex-1 mr-8 xl:mr-32 gap-10">
                    <div className="flex-1" />
                    <UserProfile />
                </nav>
            </header>
        </div>
    )
}

function UserProfile() {
    const { loading, user, setLoading } = useAuth()

    if (loading) {
        return (
            <div className="flex items-center space-x-2">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="space-y-2">
                    <Skeleton className="h-4 w-[200px]" />
                    <Skeleton className="h-4 w-[180px]" />
                </div>
            </div>
        )
    }
    return (
        <a href={user ? "#" : "/login"} className="flex flex-row items-center">
            <Icon icon="mdi:account-circle" style={{ fontSize: '40px', color: '#192f59' }} />
            <div className="text-[#192f59] font-semibold ml-2">
                {
                    user
                        ?
                        <div className="flex flex-col items-start">
                            <p>
                                {`${user.email}`}
                            </p>
                            <p onClick={async () => {
                                setLoading(true)
                                await supabase.auth.signOut()
                                setLoading(false)
                            }} className="text-xs">
                                Click here to logout
                            </p>
                        </div>
                        :
                        <p>Login</p>
                }
            </div>
        </a>
    )
}

function MenuIcon(props: any) {
    return (
        <svg
            {...props}
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <line x1="4" x2="20" y1="12" y2="12" />
            <line x1="4" x2="20" y1="6" y2="6" />
            <line x1="4" x2="20" y1="18" y2="18" />
        </svg>
    )
}