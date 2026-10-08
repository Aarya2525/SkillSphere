import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';
import { environment } from '../../../environments/environment';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpMock: HttpTestingController;
  let mockRouter: jasmine.SpyObj<Router>;

  beforeEach(() => {
    localStorage.clear();
    mockRouter = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        AuthService,
        { provide: Router, useValue: mockRouter },
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

  it('should silently refresh token and retry the original request on 401 response', () => {
    localStorage.setItem('skillsphere_access_token', 'expired_token');
    localStorage.setItem('skillsphere_refresh_token', 'valid_refresh_token');

    let responseData: any = null;
    httpClient.get('/api/protected/').subscribe(data => {
      responseData = data;
    });

    // 1. Initial request with expired token fails with 401
    const initialReq = httpMock.expectOne('/api/protected/');
    expect(initialReq.request.headers.get('Authorization')).toBe('Bearer expired_token');
    initialReq.flush('Token expired', { status: 401, statusText: 'Unauthorized' });

    // 2. Interceptor triggers refresh
    const refreshReq = httpMock.expectOne(`${environment.apiUrl}/auth/token/refresh/`);
    expect(refreshReq.request.method).toBe('POST');
    expect(refreshReq.request.body).toEqual({ refresh: 'valid_refresh_token' });
    refreshReq.flush({ access: 'new_refreshed_token_456' });

    // 3. Interceptor retries original request with new token
    const retriedReq = httpMock.expectOne('/api/protected/');
    expect(retriedReq.request.headers.get('Authorization')).toBe('Bearer new_refreshed_token_456');
    retriedReq.flush({ success: true, message: 'Retried successfully' });

    expect(responseData).toEqual({ success: true, message: 'Retried successfully' });
    expect(localStorage.getItem('skillsphere_access_token')).toBe('new_refreshed_token_456');
    expect(mockRouter.navigate).not.toHaveBeenCalled();
  });

  it('should clear stored credentials and redirect on 401 when no refresh token exists', () => {
    localStorage.setItem('skillsphere_access_token', 'expired_token');
    localStorage.setItem('skillsphere_current_user', JSON.stringify({ id: 1 }));

    httpClient.get('/api/protected/').subscribe({
      next: () => fail('should have failed with 401'),
      error: (err) => {
        expect(err.status).toBe(401);
      }
    });

    const req = httpMock.expectOne('/api/protected/');
    req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    // No refresh request should have occurred
    httpMock.expectNone(`${environment.apiUrl}/auth/token/refresh/`);

    expect(localStorage.getItem('skillsphere_access_token')).toBeNull();
    expect(localStorage.getItem('skillsphere_refresh_token')).toBeNull();
    expect(localStorage.getItem('skillsphere_current_user')).toBeNull();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('should clear stored credentials and redirect when refresh token call fails', () => {
    localStorage.setItem('skillsphere_access_token', 'expired_token');
    localStorage.setItem('skillsphere_refresh_token', 'revoked_refresh_token');

    httpClient.get('/api/protected/').subscribe({
      next: () => fail('should have failed'),
      error: (err) => {
        expect(err.status).toBe(401);
      }
    });

    const initialReq = httpMock.expectOne('/api/protected/');
    initialReq.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    const refreshReq = httpMock.expectOne(`${environment.apiUrl}/auth/token/refresh/`);
    refreshReq.flush('Refresh token invalid', { status: 401, statusText: 'Unauthorized' });

    expect(localStorage.getItem('skillsphere_access_token')).toBeNull();
    expect(localStorage.getItem('skillsphere_refresh_token')).toBeNull();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('should not retry infinitely if the retried request fails with 401 again', () => {
    localStorage.setItem('skillsphere_access_token', 'expired_token');
    localStorage.setItem('skillsphere_refresh_token', 'valid_refresh');

    httpClient.get('/api/protected/').subscribe({
      next: () => fail('should have failed on retry'),
      error: (err) => {
        expect(err.status).toBe(401);
      }
    });

    // 1. Initial 401
    const initialReq = httpMock.expectOne('/api/protected/');
    initialReq.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

    // 2. Refresh succeeds
    const refreshReq = httpMock.expectOne(`${environment.apiUrl}/auth/token/refresh/`);
    refreshReq.flush({ access: 'new_token_789' });

    // 3. Retried request fails with 401 again
    const retriedReq = httpMock.expectOne('/api/protected/');
    retriedReq.flush('Still unauthorized', { status: 401, statusText: 'Unauthorized' });

    // Should NOT trigger another refresh request
    httpMock.expectNone(`${environment.apiUrl}/auth/token/refresh/`);

    expect(localStorage.getItem('skillsphere_access_token')).toBeNull();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/login']);
  });

  it('should not attempt refresh on auth endpoints', () => {
    httpClient.post(`${environment.apiUrl}/auth/token/`, { username: 'a', password: 'b' }).subscribe({
      next: () => fail('should fail'),
      error: (err) => {
        expect(err.status).toBe(401);
      }
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/token/`);
    req.flush('Bad credentials', { status: 401, statusText: 'Unauthorized' });

    httpMock.expectNone(`${environment.apiUrl}/auth/token/refresh/`);
  });
});
