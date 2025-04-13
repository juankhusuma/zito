import { Flag, Scale } from "lucide-react"
import PrimaryButton from "../components/button"

export default function Home() {
    return (
        <div className="flex flex-col items-center justify-center h-full pb-20">
            <div className='relative w-full h-fit lg:h-[400px] z-0 flex items-center justify-center'>
                <div className='absolute z-[100] bg-[#192f59d5] top-0 left-0 w-full h-full'></div>
                <img className='absolute z-0 !w-full !h-full aspect-video object-cover object-center' src="/hukum.jpg" alt='law' />
                <div className='relative gap-5 lg:gap-28 z-[200] p-10 lg:p-5 w-full h-full items-center justify-center text-center flex flex-col lg:flex-row text-white'>
                    <h1 className='font-bold text-3xl lg:text-4xl flex-wrap lg:max-w-[50%]'>Legal Generative-AI Search</h1>
                    <div className='lg:max-w-[50%]'>
                        <h1 className='lg:font-semibold font-font-medium text-wrap text-left text-lg lg:text-xl'> Buka wawasan hukum yang tak tertandingi dengan basis data hukum berbasis Generative-AI Search, di mana kecerdasan buatan modern bertemu dengan basis data hukum yang lengkap untuk merevolusi pengalaman riset hukum Anda.</h1>
                        <a href="/chat" className="flex items-center lg:justify-start justify-center w-full">
                            <PrimaryButton
                                type='button'
                                className='mt-8'
                            >
                                <p className="lg:text-base text-sm font-semibold">Coba sekarang</p>
                            </PrimaryButton>
                        </a>
                    </div>
                </div>
            </div>
            <div className="w-full px-8 lg:px-32 pt-10">
                <div className='flex items-center w-full gap-5'>
                    <h1 className='text-3xl text-[#192f59] font-bold'>Fitur</h1>
                    <div className='bg-[#d61b23] w-full flex-1 h-1 rounded-full' />
                </div>
                <p className='text-[#d61b23] my-2'>Asisten Hukum Pintar Anda, Khusus untuk Undang-Undang Indonesia</p>
                <div className='flex lg:text-base text-sm lg:flex-row flex-col gap-10 mt-10'>
                    <div className='flex flex-col w-full lg:w-1/3 min-h-[200px] rounded-lg p-2 lg:p-6'>
                        <div className='flex items-center gap-5 mb-4'>
                            <div className='bg-[#e6e6e6] p-3 flex items-center justify-center w-fit rounded-full'>
                                <Scale size={30} color='#d61b23' className='font-semibold' />
                            </div>
                            <h2 className='text-xl text-[#383838] font-semibold'>Jawaban Kontekstual</h2>
                        </div>
                        <p className='text-[#383838] mt-3 min-h-[40px]'>Menjawab pertanyaan hukum dengan memahami konteks pertanyaan dalam bahasa alami, tanpa terbatas pada pencarian kata kunci. Sistem merespons berdasarkan pemahaman terhadap isi dokumen hukum Indonesia.</p>
                        <ul className='mt-5 flex flex-col gap-3 flex-grow'>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag className="min-w-5 w-5" color="#d61b23" /><p>Memahami pertanyaan dalam bahasa alami (natural language)</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag className="min-w-5 w-5" color="#d61b23" /><p>Menghasilkan respons berbasis isi dokumen hukum Indonesia</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag className="min-w-5 w-5" color="#d61b23" /><p>Relevan untuk pertanyaan terbuka maupun spesifik</p></li>
                        </ul>
                    </div>
                    <div className='flex flex-col w-full lg:w-1/3 min-h-[200px] rounded-lg p-2 lg:p-6'>
                        <div className='flex items-center gap-5 mb-4'>
                            <div className='bg-[#e6e6e6] p-3 flex items-center justify-center w-fit rounded-full'>
                                <Scale size={30} color='#d61b23' className='font-semibold' />
                            </div>
                            <h2 className='text-xl text-[#383838] font-semibold'>Akses ke Dokumen Hukum</h2>
                        </div>
                        <p className='text-[#383838] mt-3 min-h-[40px]'>Menggunakan sumber terbuka seperti Undang-Undang, peraturan, dan dokumen hukum lainnya sebagai basis data. Jawaban yang diberikan dilandasi referensi dari dokumen tersebut.</p>
                        <ul className='mt-5 flex flex-col gap-3 flex-grow'>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag className="min-w-5 w-5" color="#d61b23" /><p>Menggunakan Undang-Undang, peraturan, dan putusan yang tersedia publik</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag className="min-w-5 w-5" color="#d61b23" /><p>Fokus pada sumber hukum primer dari pemerintah</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag className="min-w-5 w-5" color="#d61b23" /><p>Diupdate secara berkala untuk menjaga relevansi data</p></li>
                        </ul>
                    </div>
                    <div className='flex flex-col w-full lg:w-1/3 min-h-[200px] rounded-lg p-2 lg:p-6'>
                        <div className='flex items-center gap-5 mb-4'>
                            <div className='bg-[#e6e6e6] p-3 flex items-center justify-center w-fit rounded-full'>
                                <Scale size={30} color='#d61b23' className='font-semibold' />
                            </div>
                            <h2 className='text-xl text-[#383838] font-semibold'>Rujukan Tersurat</h2>
                        </div>
                        <p className='text-[#383838] mt-3 min-h-[40px]'>Setiap jawaban disertai kutipan atau petunjuk sumber hukum yang relevan, untuk memudahkan verifikasi dan penelusuran lebih lanjut oleh pengguna.</p>
                        <ul className='mt-5 flex flex-col gap-3 flex-grow'>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag className="min-w-5 w-5" color="#d61b23" /><p>Menyediakan kutipan langsung dari dokumen hukum</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag className="min-w-5 w-5" color="#d61b23" /><p>Mencantumkan nomor pasal atau judul peraturan jika tersedia</p></li>
                            <li className='flex text-[#383838] gap-2 items-center'><Flag className="min-w-5 w-5" color="#d61b23" /><p>Memudahkan verifikasi dan pendalaman secara manual</p></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    )
}