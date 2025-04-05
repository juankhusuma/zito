import React from 'react';
import { useAuth } from './hoc/AuthProvider';
import { useNavigate } from "react-router"
import supabase from './common/supabase';

function App() {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const [sessions, setSessions] = React.useState<any[]>([])
  const [sessionTitle, setSessionTitle] = React.useState("")

  React.useEffect(() => {
    if (!loading && !user) {
      console.log("User not found, redirecting to login")
      navigate("/login")
    }

    if (user) {
      supabase.from("session").select("*").then(({ data, error }) => {
        if (error) {
          console.error("Error fetching sessions:", error)
          return
        }
        setSessions(data)
      })
    }
  }, [user, loading])

  if (loading) {
    return (
      <div className='font-mono p-5'>
        Loading...
      </div>
    )
  }

  return (
    <div className='font-mono p-5 flex items-center flex-col justify-center h-screen'>
      <table>
        <thead>
          <tr>
            <th className='border border-black p-2'>ID</th>
            <th className='border border-black p-2'>Email</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className='border border-black p-2'>{user?.id}</td>
            <td className='border border-black p-2'>{user?.email}</td>
          </tr>
        </tbody>
      </table>
      <h1 className='mt-5 font-bold'>Create a new chat session</h1>
      <form onSubmit={async (e) => {
        e.preventDefault()
        supabase.from("session").insert({
          title: sessionTitle,
        }).select().then(({ data, error }) => {
          if (error) {
            console.error("Error creating session:", error)
            return
          }
          setSessions((prev) => [...prev, ...data])
          setSessionTitle("")
        })
      }}>
        <input
          onChange={(e) => setSessionTitle(e.target.value)}
          value={sessionTitle}
          type="text" placeholder='Title' className='border border-black p-2 my-2' />
        <button type="submit" className='border border-black p-2 bg-gray-200 cursor-pointer'>Create</button>
      </form>
      <h1 className='my-5 font-bold'>Chat Sessions</h1>
      <table className='w-1/2'>
        <thead>
          <tr>
            <th className='border border-black p-2'>ID</th>
            <th className='border border-black p-2'>Title</th>
            <th className='border border-black p-2'>Created At</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((session) => (
            <tr onClick={() => navigate(`/chat/${session.id}`)} key={session.id} className='hover:bg-gray-100 cursor-pointer'>
              <td className='border border-black p-2'>{session.id}</td>
              <td className='border border-black p-2'>{session.title}</td>
              <td className='border border-black p-2'>{session.created_at}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default App
