import { Flag, Scale } from "lucide-react"
import PrimaryButton from "../components/button"

export default function Home() {
    return (
        <div className="flex flex-col items-center justify-center h-full">
            <div className='relative w-full h-[400px] z-0 flex items-center justify-center'>
                <div className='absolute z-[100] bg-[#192f59d5] top-0 left-0 w-full h-full'></div>
                <img className='absolute z-0 !w-full !h-full aspect-video object-cover object-center' src="/hukum.jpg" alt='law' />
                <div className='relative gap-28 z-[200] p-5 w-full h-full items-center justify-center text-center flex text-white'>
                    <h1 className='font-bold text-4xl flex-wrap max-w-[50%]'>Legal Generative-AI Search</h1>
                    <div className='max-w-[50%]'>
                        <h1 className='font-semibold text-wrap text-left text-xl'> Buka wawasan hukum yang tak tertandingi dengan basis data hukum berbasis Generative-AI Search, di mana kecerdasan buatan modern bertemu dengan basis data hukum yang lengkap untuk merevolusi pengalaman riset hukum Anda.</h1>
                        <a href="/search">
                            <PrimaryButton
                                type='button'
                                className='mt-8'
                            >
                                Coba sekarang
                            </PrimaryButton>
                        </a>
                    </div>
                </div>
            </div>
            <div className="w-full px-32 pt-10">
                <div className='flex items-center w-full gap-5'>
                    <h1 className='text-3xl text-[#192f59] font-bold'>Fitur</h1>
                    <div className='bg-[#d61b23] w-full flex-1 h-1 rounded-full' />
                </div>
                <p className='text-[#d61b23] my-2'>Lorem ipsum dolor sit amet consectetur adipisicing elit. Molestiae aliquid enim explicabo!</p>
                <div className='flex gap-10 mt-10'>
                    <div>
                        <div className='flex items-center gap-5'>
                            <div className='bg-[#e6e6e6] p-3 flex items-center justify-center w-fit rounded-full'>
                                <Scale size={30} color='#d61b23' className='font-semibold' />
                            </div>
                            <h2 className='text-xl text-[#383838] font-semibold'>Legal Knowledge Extraction</h2>
                        </div>
                        <p className='text-[#383838] mt-3'>This research area focuses on extracting useful information and knowledge from vast amounts of legal texts and managing this knowledge efficiently. Research can be directed towards developing advanced search algorithms, knowledge graphs, data creation pipelines and databases specifically tailored for legal texts. Recent research topics include:</p>
                        <ul className='mt-5 flex flex-col gap-3'>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag color="#d61b23" /><p>Legal Search Algorithms</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag color="#d61b23" /><p>Legal Search Algorithms</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag color="#d61b23" /><p>Legal Search Algorithms</p></li>
                        </ul>
                    </div>
                    <div>
                        <div className='flex items-center gap-5'>
                            <div className='bg-[#e6e6e6] p-3 flex items-center justify-center w-fit rounded-full'>
                                <Scale size={30} color='#d61b23' className='font-semibold' />
                            </div>
                            <h2 className='text-xl text-[#383838] font-semibold'>Legal Knowledge Extraction</h2>
                        </div>
                        <p className='text-[#383838] mt-3'>This research area focuses on extracting useful information and knowledge from vast amounts of legal texts and managing this knowledge efficiently. Research can be directed towards developing advanced search algorithms, knowledge graphs, data creation pipelines and databases specifically tailored for legal texts. Recent research topics include:</p>
                        <ul className='mt-5 flex flex-col gap-3'>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag color="#d61b23" /><p>Legal Search Algorithms</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag color="#d61b23" /><p>Legal Search Algorithms</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag color="#d61b23" /><p>Legal Search Algorithms</p></li>
                        </ul>
                    </div>
                    <div>
                        <div className='flex items-center gap-5'>
                            <div className='bg-[#e6e6e6] p-3 flex items-center justify-center w-fit rounded-full'>
                                <Scale size={30} color='#d61b23' className='font-semibold' />
                            </div>
                            <h2 className='text-xl text-[#383838] font-semibold'>Legal Knowledge Extraction</h2>
                        </div>
                        <p className='text-[#383838] mt-3'>This research area focuses on extracting useful information and knowledge from vast amounts of legal texts and managing this knowledge efficiently. Research can be directed towards developing advanced search algorithms, knowledge graphs, data creation pipelines and databases specifically tailored for legal texts. Recent research topics include:</p>
                        <ul className='mt-5 flex flex-col gap-3'>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag color="#d61b23" /><p>Legal Search Algorithms</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag color="#d61b23" /><p>Legal Search Algorithms</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag color="#d61b23" /><p>Legal Search Algorithms</p></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    )
}