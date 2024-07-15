import { Router } from "express";
import GptService from "../services/gpt-services";
import GptController from "../controllers/gpt-controller";

const gptRouter = Router();
const gptService = new GptService();
const gptController = new GptController(gptService);

gptRouter.post('/gpt-creating/', gptController.getCode);

export default gptRouter;