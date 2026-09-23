import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface AIAssistantAskRequest {
  lesson_id: number;
  message: string;
}

export interface AIAssistantAskResponse {
  answer: string;
  lesson_id: number;
}

@Injectable({
  providedIn: 'root'
})
export class AIAssistantService {

  private readonly http = inject(HttpClient);

  private readonly apiUrl =
    `${environment.apiUrl}/ai`;

  askQuestion(
    lessonId: number,
    message: string
  ): Observable<AIAssistantAskResponse> {

    return this.http.post<AIAssistantAskResponse>(
      `${this.apiUrl}/ask/`,
      {
        lesson_id: lessonId,
        message
      }
    );
  }
}
