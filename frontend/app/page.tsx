export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          StroyZakup
        </h1>
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
          Servis organizatsii zakupok stroymaterialov. Otpravte spisok materialov — naydyom luchshie tseny u postavshchikov v vashem regione.
        </p>
        <div className="flex gap-4 justify-center">
          <a href="/login" className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition">
            Voyti
          </a>
          <a href="/register" className="px-8 py-3 bg-white text-blue-600 border-2 border-blue-600 rounded-lg font-semibold hover:bg-blue-50 transition">
            Registratsiya
          </a>
        </div>
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
          {[
            { title: 'Raspoznavanie', desc: 'Avtomaticheskiy razbor spiska materialov s pomoshchyu AI.' },
            { title: 'Poisk postavshchikov', desc: 'Naydyom proizvoditeley i dilerov v radIuse vashego obekta.' },
            { title: 'Sravnenie tsen', desc: 'Konkurentnyy list dlya vybora luchshego predlozheniya.' },
          ].map((f) => (
            <div key={f.title} className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <h3 className="font-bold text-lg mb-2">{f.title}</h3>
              <p className="text-gray-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
