import mongoose from "mongoose";
import ICode from "../interfaces/code.interface";

const codeSchema = new mongoose.Schema(
    {
        code: {type: String, require: true}
    },
    {
        timestamps: true,
    }
);

const Code = mongoose.model<ICode>("Code", codeSchema);
export default Code;