import { COMPOSITION_BUFFER_MODE } from "@angular/forms"
import { version } from "typescript"

export class Judge_json {

    version: string;
    comp_id: number;
    comp_name: string;
    judge_id: number;
    judge_hash: string;
    judge_first_name: string;
    judge_last_name: string;
    days_with_disciplines_lanes: any;
   // days_with_disciplines_lanes: self.data_.getDaysWithDisciplinesLanes()

    constructor(
        version: string,
        comp_id: number,
        comp_name: string,
        judge_id: number,
        judge_hash: string,
        judge_first_name: string,
        judge_last_name: string,
        dwd: any)
{
        this.version = version
        this.comp_id = comp_id
        this.comp_name = comp_name
        this.judge_id = judge_id
        this.judge_hash = judge_hash
        this.judge_first_name = judge_first_name
        this.judge_last_name = judge_last_name
        this.days_with_disciplines_lanes = dwd;
}
}