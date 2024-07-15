import mongoose from "mongoose";

interface ICode extends mongoose.Document {
    code: string;
}

export default ICode;