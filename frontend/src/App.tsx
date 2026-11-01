import { useState } from "react";

import { AppBar, type Tab } from "./components/AppBar";
import { LoginPage } from "./features/auth/LoginPage";
import { DormApp } from "./features/dorm/DormApp";
import { SalespersonApp, type SalesView } from "./features/sales/SalespersonApp";
import { useSession } from "./hooks/useSession";

const SALESPERSON_TABS: Tab[] = [
  { id: "inbox", label: "Inbox" },
  { id: "new", label: "New request" },
];
const DORM_TABS: Tab[] = [{ id: "inbox", label: "Inbox" }];

export function App() {
  const { user, signOut } = useSession();
  const [view, setView] = useState<SalesView>("inbox");
  // Choosing a tab remounts the page, which is how "Inbox" always lands back on the list.
  const [navigation, setNavigation] = useState(0);

  const goTo = (tab: string) => {
    window.history.replaceState(null, "", window.location.pathname);
    setView(tab as SalesView);
    setNavigation((count) => count + 1);
  };

  if (user === null) return <LoginPage />;

  const isSalesperson = user.role === "salesperson";
  return (
    <div className="app">
      <AppBar
        user={user}
        tabs={isSalesperson ? SALESPERSON_TABS : DORM_TABS}
        current={isSalesperson ? view : "inbox"}
        onChange={goTo}
        onSignOut={signOut}
      />
      <main className="page">
        {isSalesperson ? <SalespersonApp key={navigation} view={view} onViewChange={setView} /> : <DormApp key={navigation} />}
      </main>
    </div>
  );
}
