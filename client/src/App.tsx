import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import AutoNetApp from "./pages/AutoNetApp";

function AppRouter() {
  return <Switch><Route path="/:rest*" component={AutoNetApp} /><Route component={AutoNetApp} /></Switch>;
}

export default function App() {
  return <ErrorBoundary><ThemeProvider defaultTheme="light"><TooltipProvider><AppRouter /></TooltipProvider></ThemeProvider></ErrorBoundary>;
}
