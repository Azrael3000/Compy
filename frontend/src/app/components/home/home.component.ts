import { Component, Injectable } from '@angular/core';
import { Judge } from '../../inserters/judges';
import { NgFor } from '@angular/common';
import { Competition } from '../../competitions/competitions';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { HttpClient } from '@angular/common/http';
import { Judge_json } from '../../data_models/judge_json';


@Component({
  selector: 'app-home',
  standalone: true,
  imports: [NgFor,MatSlideToggleModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})

@Injectable({providedIn: 'root'})
export class HomeComponent {
  
  //judges: Judge[];
  comp: Competition;
  version: string;
  judge: Judge;


  constructor(private http: HttpClient){
    this.judge = new Judge('Eva','foo');
    this.comp = new Competition('TEST','Vienna','2024-01-12','AIDA');
    
    this.version = '';

    let hash ="f69d4596fb43e780a4900b50d66fbde179b3f67edc95e2169690f9914b11abeb";

    http.get<Judge_json>('http://localhost:5000/judge_json/3/1',{params: {hash: hash}})
      .subscribe(config =>
        {
          console.log('version:', config.version);
          this.version = config.version;
          this.judge = new Judge(config.judge_first_name, config.judge_last_name);
          this.comp.name = config.comp_name;
        });
  }
}


