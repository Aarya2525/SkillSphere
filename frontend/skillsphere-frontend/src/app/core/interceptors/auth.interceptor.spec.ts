import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { authInterceptor } from './auth.interceptor';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting()
      ]
    });
    httpClient = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should attach Bearer token to request headers when access token exists', () => {
    localStorage.setItem('skillsphere_access_token', 'test_jwt_access_token_123');

    httpClient.get('/api/test/').subscribe();

    const req = httpMock.expectOne('/api/test/');
    expect(req.request.headers.has('Authorization')).toBeTrue();
    expect(req.request.headers.get('Authorization')).toBe('Bearer test_jwt_access_token_123');
    req.flush({});
  });

  it('should not attach Authorization header when no access token exists', () => {
    httpClient.get('/api/test/').subscribe();

    const req = httpMock.expectOne('/api/test/');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });
});
