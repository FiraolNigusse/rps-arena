export default function Home({ user }) {
    if (!user) {
      return <div>Loading...</div>;
    }
  
    return (
      <div style={{ padding: 20 }}>
        <h2>{user.username}</h2>
  
        <p>🪙 Coins: <strong>{user.coins}</strong></p>
        <p>⭐ Rating: <strong>{user.rating}</strong></p>
  
        <button
          style={{
            width: "100%",
            padding: 16,
            fontSize: 18,
            marginTop: 20
          }}
        >
          ▶ PLAY
        </button>
  
        <button
          style={{
            width: "100%",
            padding: 12,
            marginTop: 10
          }}
          onClick={() => window.location.href = "/wallet"}
        >
          Wallet
        </button>
      </div>
    );
  }
  