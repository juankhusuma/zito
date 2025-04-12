import { useParams } from "react-router"

export function SessionChatPage() {
    const { sessionId } = useParams()
    return (
        <div>
            {sessionId}
        </div>
    )
}