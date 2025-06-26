import { BrowserRouter, Routes, Route } from "react-router-dom";
import MessageParsePage from "./pages/MessageParse";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/parse" element={<MessageParsePage />} />
        {/* İleride diğer sayfaları da buraya ekleyeceğiz */}
      </Routes>
    </BrowserRouter>
  );
}

export default App;
