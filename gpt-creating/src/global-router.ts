import { Router } from "express";
import gptRouter from "./routes/gpt-routes";

const globalRouter = Router();

globalRouter.use(gptRouter)

export default globalRouter; 