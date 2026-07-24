import Link from "next/link";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-sm border">
        <h1 className="text-2xl font-bold mb-6 text-center">Vkhod</h1>
        <form action="/api/auth/login/" method="POST" className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input name="email" type="email" required className="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Parol</label>
            <input name="password" type="password" required className="w-full px-3 py-2 border rounded-lg" />
          </div>
          <button type="submit" className="w-full py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700">
            Voyti
          </button>
        </form>
        <p className="text-center text-sm text-gray-600 mt-4">
          Net akkaunta? <Link href="/register" className="text-blue-600 hover:underline">Registratsiya</Link>
        </p>
      </div>
    </div>
  )
}
