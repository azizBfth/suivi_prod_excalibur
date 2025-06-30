"""
Health check and system status routes.
"""

from fastapi import APIRouter, Depends
from datetime import datetime
import sys
import platform

from app.core.database import get_analyzer
from app.core.config import get_settings
from app.models.schemas import BaseResponse, User
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/health", tags=["Health & Status"])


@router.get("/", response_model=BaseResponse)
async def health_check():
    """Basic health check endpoint."""
    try:
        # Try to get analyzer to check database connectivity
        from app.core.database import _analyzer
        database_connected = _analyzer is not None

        return BaseResponse(success=True, data={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database_connected": database_connected,
            "version": "2.0.0"
        })
    except Exception as e:
        return BaseResponse(success=False, data={
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database_connected": False,
            "error": str(e),
            "version": "2.0.0"
        })


@router.get("/detailed", response_model=BaseResponse)
async def detailed_health_check(current_user: User = Depends(get_current_user)):
    """Detailed health check with system information."""
    try:
        settings = get_settings()
        
        # Try to get analyzer to check database connectivity
        from app.core.database import _analyzer
        database_connected = _analyzer is not None
        
        # System information
        system_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "architecture": platform.architecture(),
            "hostname": platform.node()
        }
        
        # Application configuration (without sensitive data)
        app_config = {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "debug": settings.debug,
            "host": settings.host,
            "port": settings.port,
            "database_configured": all([
                settings.db_uid,
                settings.db_pwd,
                settings.db_host,
                settings.db_server_name,
                settings.db_database_name
            ])
        }
        
        return BaseResponse(success=True, data={
            "status": "healthy" if database_connected else "degraded",
            "timestamp": datetime.now().isoformat(),
            "database_connected": database_connected,
            "system_info": system_info,
            "app_config": app_config,
            "version": settings.app_version
        })
    except Exception as e:
        return BaseResponse(success=False, data={
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "version": "2.0.0"
        })


@router.get("/database", response_model=BaseResponse)
async def database_health_check(current_user: User = Depends(get_current_user), analyzer=Depends(get_analyzer)):
    """Check database connectivity and perform a simple query."""
    try:
        # Try to execute a simple query
        test_df = analyzer.execute_query("SELECT 1 as test_value")
        
        if test_df is not None and not test_df.empty:
            database_status = "connected"
            test_result = test_df.iloc[0]['test_value']
        else:
            database_status = "query_failed"
            test_result = None
        
        return BaseResponse(success=True, data={
            "database_status": database_status,
            "test_query_result": test_result,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return BaseResponse(success=False, data={
            "database_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })


@router.get("/data-sources", response_model=BaseResponse)
async def check_data_sources(current_user: User = Depends(get_current_user), analyzer=Depends(get_analyzer)):
    """Check availability of main data sources."""
    try:
        data_sources = {}
        
        # Check OF_DA table
        try:
            of_count = analyzer.execute_query("SELECT COUNT(*) as count FROM gpao.OF_DA WHERE NUMERO_OFDA LIKE 'F%'")
            data_sources["OF_DA"] = {
                "status": "available",
                "record_count": of_count.iloc[0]['count'] if of_count is not None else 0
            }
        except Exception as e:
            data_sources["OF_DA"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check HISTO_OF_DA table
        try:
            histo_count = analyzer.execute_query("SELECT COUNT(*) as count FROM gpao.HISTO_OF_DA")
            data_sources["HISTO_OF_DA"] = {
                "status": "available",
                "record_count": histo_count.iloc[0]['count'] if histo_count is not None else 0
            }
        except Exception as e:
            data_sources["HISTO_OF_DA"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check SALARIES table
        try:
            salaries_count = analyzer.execute_query("SELECT COUNT(*) as count FROM gpao.SALARIES WHERE ACTIF = 1")
            data_sources["SALARIES"] = {
                "status": "available",
                "record_count": salaries_count.iloc[0]['count'] if salaries_count is not None else 0
            }
        except Exception as e:
            data_sources["SALARIES"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Overall status
        all_available = all(source.get("status") == "available" for source in data_sources.values())
        overall_status = "all_available" if all_available else "some_issues"
        
        return BaseResponse(success=True, data={
            "overall_status": overall_status,
            "data_sources": data_sources,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return BaseResponse(success=False, data={
            "overall_status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })


@router.get("/performance", response_model=BaseResponse)
async def performance_check(current_user: User = Depends(get_current_user), analyzer=Depends(get_analyzer)):
    """Check system performance with timing tests."""
    try:
        import time
        
        performance_tests = {}
        
        # Test simple query performance
        start_time = time.time()
        test_df = analyzer.execute_query("SELECT COUNT(*) as count FROM gpao.OF_DA WHERE NUMERO_OFDA LIKE 'F%'")
        query_time = time.time() - start_time
        
        performance_tests["simple_query"] = {
            "duration_seconds": round(query_time, 3),
            "status": "fast" if query_time < 1.0 else "slow" if query_time < 5.0 else "very_slow"
        }
        
        # Test complex query performance (if data exists)
        from datetime import timedelta
        start_time = time.time()
        complex_df = analyzer.get_comprehensive_of_data(
            (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            datetime.now().strftime('%Y-%m-%d'),
            'C'
        )
        complex_query_time = time.time() - start_time
        
        performance_tests["complex_query"] = {
            "duration_seconds": round(complex_query_time, 3),
            "status": "fast" if complex_query_time < 2.0 else "slow" if complex_query_time < 10.0 else "very_slow",
            "record_count": len(complex_df) if complex_df is not None else 0
        }
        
        # Overall performance status
        overall_performance = "good"
        if any(test.get("status") == "very_slow" for test in performance_tests.values()):
            overall_performance = "poor"
        elif any(test.get("status") == "slow" for test in performance_tests.values()):
            overall_performance = "acceptable"
        
        return BaseResponse(success=True, data={
            "overall_performance": overall_performance,
            "performance_tests": performance_tests,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return BaseResponse(success=False, data={
            "overall_performance": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })


@router.get("/version", response_model=BaseResponse)
async def get_version_info():
    """Get application version and build information."""
    try:
        settings = get_settings()
        
        version_info = {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "api_version": "v1",
            "build_date": "2024-01-01",  # You can make this dynamic
            "python_version": sys.version.split()[0],
            "fastapi_version": "0.104.1",  # You can get this dynamically
            "dependencies": {
                "pandas": "2.1.0",
                "pyodbc": "4.0.39",
                "pydantic": "2.4.0"
            }
        }
        
        return BaseResponse(success=True, data=version_info)
    except Exception as e:
        return BaseResponse(success=False, data={
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })
