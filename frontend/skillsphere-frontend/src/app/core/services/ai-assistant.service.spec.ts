import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AIAssistantService, AIAssistantAskResponse } from './ai-assistant.service';
import { environment } from '../../../environments/environment';

describe('AIAssistantService', () => {
  let service: AIAssistantService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AIAssistantService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(AIAssistantService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('askQuestion should post lesson_id and message to /ai/ask/', () => {
    const mockResponse: AIAssistantAskResponse = {
      answer: 'A component is a self-contained UI building block in Angular.',
      lesson_id: 10
    };

    service.askQuestion(10, 'What is a component?').subscribe(res => {
      expect(res.answer).toBe(mockResponse.answer);
      expect(res.lesson_id).toBe(10);
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/ai/ask/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      lesson_id: 10,
      message: 'What is a component?'
    });
    req.flush(mockResponse);
  });

  it('askQuestion should propagate HTTP error responses (e.g. 429 rate limited)', () => {
    service.askQuestion(10, 'Rapid question').subscribe({
      next: () => fail('Should have failed with 429'),
      error: error => {
        expect(error.status).toBe(429);
      }
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/ai/ask/`);
    req.flush(
      { error: { code: 'rate_limited', message: 'Request was throttled.' } },
      { status: 429, statusText: 'Too Many Requests' }
    );
  });
});
