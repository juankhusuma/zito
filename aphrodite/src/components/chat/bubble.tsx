import { cn } from "@/lib/utils";
import { UserCircle2 } from "lucide-react";
import { useAnimatedText } from "../ui/animated-text";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatBubbleProps {
    sender: "user" | "assistant";
    timestamp: string;
    isLoading?: boolean;
    isDone?: boolean;
    message: string;
}

export default function ChatBubble(props: ChatBubbleProps) {
    const text = (props.sender === "user" || props.isDone) ? props.message : useAnimatedText(props.message);
    return (
        <div className={cn("flex mb-3 text-xs lg:text-sm", props.sender === "user" ? "flex-row" : "flex-row-reverse")}>
            <div className={cn("flex items-start w-full", props.sender === "user" ? "justify-end" : "justify-start")}>
                {props.sender === "assistant" && <img src="/lexin-logo.svg" alt="lexin" className={cn(
                    "w-[20px] h-[20px] object-contain object-center mt-2",
                    !props.isDone || props.isLoading ? "animate-pulse" : ""
                )} />}
                <div
                    className={cn(
                        "rounded-lg px-3 py-2 w-fit",
                        props.sender === "assistant" ? "text-primary-foreground ml-2" : "bg-muted border-1 mr-2 max-w-1/2"
                    )}
                >
                    {props.isLoading ? (
                        <div className="flex items-center space-x-2">
                            <MessageLoading />
                        </div>
                    ) : (
                        props.sender === "user" ? (<p>{text}</p>)
                            : (
                                <div className="prose prose-sm max-w-full prose-pre:font-mono prose-code:font-mono">
                                    <Markdown remarkPlugins={[remarkGfm]}>
                                        {text}
                                    </Markdown>
                                </div>
                            )
                    )}
                </div>
                {props.sender === "user" && <UserCircle2 className="text-sm font-light mt-2 text-gray-600" />}
            </div>
        </div>
    )
}

function MessageLoading() {
    return (
        <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
            className="text-[#192f59]"
        >
            <circle cx="4" cy="12" r="2" fill="currentColor">
                <animate
                    id="spinner_qFRN"
                    begin="0;spinner_OcgL.end+0.25s"
                    attributeName="cy"
                    calcMode="spline"
                    dur="0.6s"
                    values="12;6;12"
                    keySplines=".33,.66,.66,1;.33,0,.66,.33"
                />
            </circle>
            <circle cx="12" cy="12" r="2" fill="currentColor">
                <animate
                    begin="spinner_qFRN.begin+0.1s"
                    attributeName="cy"
                    calcMode="spline"
                    dur="0.6s"
                    values="12;6;12"
                    keySplines=".33,.66,.66,1;.33,0,.66,.33"
                />
            </circle>
            <circle cx="20" cy="12" r="2" fill="currentColor">
                <animate
                    id="spinner_OcgL"
                    begin="spinner_qFRN.begin+0.2s"
                    attributeName="cy"
                    calcMode="spline"
                    dur="0.6s"
                    values="12;6;12"
                    keySplines=".33,.66,.66,1;.33,0,.66,.33"
                />
            </circle>
        </svg>
    );
}
