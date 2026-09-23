import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { authGuard, roleGuard } from './auth-guard';
import { AuthService, User } from '../services/auth.service';

describe('Route Guards', () => {
  let mockAuthService: jasmine.SpyObj<AuthService>;
  let router: Router;

  beforeEach(() => {
    mockAuthService = jasmine.createSpyObj('AuthService', ['isLoggedIn', 'getCurrentUserSnapshot']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: mockAuthService }
      ]
    });

    router = TestBed.inject(Router);
  });

  describe('authGuard', () => {
    it('should allow navigation when user is logged in', () => {
      mockAuthService.isLoggedIn.and.returnValue(true);

      const result = TestBed.runInInjectionContext(() => authGuard({} as any, {} as any));
      expect(result).toBeTrue();
    });

    it('should redirect to /login when user is not logged in', () => {
      mockAuthService.isLoggedIn.and.returnValue(false);

      const result = TestBed.runInInjectionContext(() => authGuard({} as any, {} as any)) as UrlTree;
      expect(result.toString()).toBe('/login');
    });
  });

  describe('roleGuard', () => {
    it('should redirect to /login when user is not logged in', () => {
      mockAuthService.isLoggedIn.and.returnValue(false);

      const guard = roleGuard(['INSTRUCTOR']);
      const result = TestBed.runInInjectionContext(() => guard({} as any, {} as any)) as UrlTree;
      expect(result.toString()).toBe('/login');
    });

    it('should allow navigation when user has an allowed role', () => {
      mockAuthService.isLoggedIn.and.returnValue(true);
      const instructorUser: User = { id: 1, username: 'inst', email: 'inst@test.com', role: 'INSTRUCTOR' };
      mockAuthService.getCurrentUserSnapshot.and.returnValue(instructorUser);

      const guard = roleGuard(['INSTRUCTOR']);
      const result = TestBed.runInInjectionContext(() => guard({} as any, {} as any));
      expect(result).toBeTrue();
    });

    it('should reject unauthorized student and redirect to /dashboard', () => {
      mockAuthService.isLoggedIn.and.returnValue(true);
      const studentUser: User = { id: 2, username: 'stud', email: 'stud@test.com', role: 'STUDENT' };
      mockAuthService.getCurrentUserSnapshot.and.returnValue(studentUser);

      const guard = roleGuard(['INSTRUCTOR']);
      const result = TestBed.runInInjectionContext(() => guard({} as any, {} as any)) as UrlTree;
      expect(result.toString()).toBe('/dashboard');
    });

    it('should reject unauthorized instructor and redirect to /instructor/dashboard', () => {
      mockAuthService.isLoggedIn.and.returnValue(true);
      const instructorUser: User = { id: 1, username: 'inst', email: 'inst@test.com', role: 'INSTRUCTOR' };
      mockAuthService.getCurrentUserSnapshot.and.returnValue(instructorUser);

      const guard = roleGuard(['STUDENT']);
      const result = TestBed.runInInjectionContext(() => guard({} as any, {} as any)) as UrlTree;
      expect(result.toString()).toBe('/instructor/dashboard');
    });
  });
});
