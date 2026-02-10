export default function Wallet({ user }) {
    if (!user) {
      return <div>Loading...</div>;
    }
  
    return (
      <div style={{ padding: 20 }}>
        <h2>Wallet</h2>
  
        <p>🪙 Coins: <strong>{user.coins}</strong></p>
  
        <p style={{ fontSize: 14, opacity: 0.7 }}>
          Coins are used to play games.
        </p>
  
        <button
          style={{
            width: "100%",
            padding: 12,
            marginTop: 20
          }}
          disabled
        >
          Buy Coins (Coming Soon)
        </button>
  
        <button
          style={{
            width: "100%",
            padding: 12,
            marginTop: 10
          }}
          disabled
        >
          Withdraw (Coming Soon)
        </button>
      </div>
    );
  }
  